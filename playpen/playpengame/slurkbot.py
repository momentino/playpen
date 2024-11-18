"""Slurk (Task)Bot template classes.

This file provides an abstract Bot class with 3 implemented classes that
inherit from one another with increasing specificity wrt to the task they are
carrying out:

- Bot is an abstract class that
  - implements the basic methods for connecting to a slurk server and handling
    message requests
  - provides an abstract method register_callbacks that handles incoming events
- TaskBot(Bot)
  - has an additional property task_id and implements the logic for letting
    the bot join a room associated to that task
  - resizes the chat and display area to give more room to the chat as the
    display are is empty for the basic setting
- GenericChatbot(TaskBot)
  - has an additional property players_per_room that tracks what rooms players
    are in (needed for handling resources like images)
  - implements logic for letting the bot join an associated task room after
    keeping track of the users
  - implements the logic for handling the /ready and /stop commands
  - implements a method to provide a token or code for a user (for external
    mapping, e.g. to MTurk HITs)
  - implements a closing mechanism that removes players from the room
- APIChatBot(GenericChatbot)
  - implements specific game logic for a starting phase (joined_room) and a
    /ready and /stop command (command)
  - this is the class that the GameMaster should instantiate
"""

from abc import ABC, abstractmethod
import random
import string

import logging

import requests  # NOQA
import socketio

from time import sleep

TASK_GREETING = """
**Welcome to the Chatbot Game!**

Please type **/ready** to begin the game.
"""
TIME_CLOSE = 1

LOG = logging.getLogger(__name__)


class Bot(ABC):
    sio = socketio.Client(logger=True)

    def __init__(self, token, user, host, port):
        """Serves as a template for bots.
        :param token: A universally unique identifier (UUID);
            e.g. `0c45b30f-d049-43d1-b80d-e3c3a3ca22a0`
        :type token: str
        :param user: ID of a `User` object created from the token
        :type user: int
        :param host: Full URL including protocol and hostname
        :type host: str
        :param port: Port used by the slurk chat server;
            If you use a docker container that publishes an internal
            port to another port on the docker host, specify the latter
        :type port: int
        """
        self.token = token
        self.user = user

        self.uri = host
        if port is not None:
            self.uri += f":{port}"
        self.uri += "/slurk/api"
        logging.info(f"Running {self.__class__.__name__} on {self.uri} with token: {self.token} ...")

        self.register_callbacks()

    @abstractmethod
    def register_callbacks(self):
        """Register all necessary event handlers."""
        pass

    def run(self):
        """Establish a connection to the slurk chat server."""
        self.sio.connect(
            self.uri,
            headers={"Authorization": f"Bearer {self.token}", "user": str(self.user)},
            namespaces="/",
        )
        self.sio.wait()

    @staticmethod
    def message_callback(success, error_msg="Unknown Error"):
        """Verify whether a call was successful.
        Will be invoked after the server has processed the event,
        any values returned by the event handler will be passed
        as arguments.
        :param success: `True` if the message was successfully sent,
            else `False`
        :type success: bool
        :param error_msg: Reason for an unsuccessful call
        :type status: str, optional
        """
        if not success:
            logging.error(f"Could not send message: {error_msg}")
            raise ValueError(error_msg)
        logging.debug("Message was sent successfully.")

    @staticmethod
    def request_feedback(response, action):
        """Verify whether a request was successful.
        :param response: Response to request
        :type response: requests.models.Response
        :param action: Action meant to be performed
        :type action: str
        """
        if not response.ok:
            logging.error(f"`{action}` unsuccessful: {response.status_code}")
            response.raise_for_status()
        logging.debug(f"`{action}` successful.")


class TaskBot(Bot):

    def __init__(self, token, user, task, host, port):
        """Serves as a template for task bots.
        :param task: Task ID
        :type task: str
        """
        super().__init__(token, user, host, port)
        self.task_id = task
        self.sio.on("new_task_room", self.join_task_room())

    def join_task_room(self):
        """Let the bot join an assigned task room."""

        LOG.info("join_task_room in TaskBot")

        def join(data):
            if self.task_id is None or data["task"] != self.task_id:
                return

            response = requests.post(
                f"{self.uri}/users/{self.user}/rooms/{data['room']}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            self.request_feedback(response, f"let {self.__class__.__name__}  join room")

        return join

    def move_divider(self, room_id, chat_area=50, task_area=50):
        """move the central divider and resize chat and task area
        the sum of char_area and task_area must sum up to 100
        """
        if chat_area + task_area != 100:
            logging.error("could not resize chat and task area: invalid parameters")
            raise ValueError("chat_area and task_area must sum up to 100")

        response = requests.patch(
            f"{self.uri}/rooms/{room_id}/attribute/id/sidebar",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"attribute": "style", "value": f"width: {task_area}%"}
        )
        self.request_feedback(response, "resize display area")
        response = requests.patch(
            f"{self.uri}/rooms/{room_id}/attribute/id/content",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"attribute": "style", "value": f"width: {chat_area}%"}
        )
        self.request_feedback(response, "resize chat area")


class GenericChatbot(TaskBot):
    """A bot that talks to a user by calling some chatbot API"""
    """The ID of the room where users for this task are waiting."""
    waiting_room = None

    def __init__(self, *args, **kwargs):
        """This bot interacts with 1 human player by calling an API to carry
        out the actual interaction

        :param players_per_room: Each room is mapped to a list of
            users. Each user is represented as a dict with the
            keys 'name', 'id', 'msg_n' and 'status'.
        :type players_per_room: dict
        """
        super().__init__(*args, **kwargs)
        self.players_per_room = dict()

    def join_task_room(self):
        """Let the bot join an assigned task room."""

        def join(data):
            if self.task_id is None or data["task"] != self.task_id:
                return

            room_id = data["room"]

            LOG.debug(f"A new task room was created with id: {data['task']}")
            LOG.debug(f"This bot is looking for task id: {self.task_id}")

            self.move_divider(room_id, 70, 30)

            self.players_per_room[room_id] = []
            for usr in data["users"]:
                self.players_per_room[room_id].append(
                    {**usr, "msg_n": 0, "status": "joined"}
                )

            response = requests.post(
                f"{self.uri}/users/{self.user}/rooms/{room_id}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            self.request_feedback(response, f"let {self.__class__.__name__} join room")

        return join

    def command_stop(self, room_id, user_id):
        """Stopping criterion. End conversation"""
        # create token and send it to user
        users = self.players_per_room[room_id]
        curr_usr = users[0]
        curr_usr["status"] = "done"
        self.confirmation_code(room_id, "done", receiver_id=user_id)
        self.close_game(room_id)

    def _command_ready(self, room_id, user_id):
        """Must be sent to begin a conversation."""
        users = self.players_per_room[room_id]
        curr_usr = users[0]

        if curr_usr["id"] != user_id:
            LOG.warning("Something is wrong here.")
            return

        # only one user has sent /ready repetitively
        if curr_usr["status"] in {"ready", "done"}:
            sleep(0.5)
            self.sio.emit(
                "text",
                {
                    "message": "You have already typed /ready.",
                    "receiver_id": curr_usr["id"],
                    "room": room_id,
                },
            )
            return
        curr_usr["status"] = "ready"

        # a first ready command was sent
        sleep(0.5)
        # give the user feedback that his command arrived
        self.sio.emit(
            "text",
            {
                "message": "Okay, let's begin!",
                "receiver_id": curr_usr["id"],
                "room": room_id,
            },
        )

    def confirmation_code(self, room_id, status, receiver_id=None):
        """Generate a code that will be sent to each player."""
        kwargs = dict()
        # either only for one user or for both
        if receiver_id is not None:
            kwargs["receiver_id"] = receiver_id

        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # post code to logs
        response = requests.post(
            f"{self.uri}/logs",
            json={
                "event": "confirmation_log",
                "room_id": room_id,
                "data": {"status_txt": status, "code": code},
                **kwargs,
            },
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.request_feedback(response, "post code to logs")

        self.sio.emit(
            "text",
            {
                "message": "Please enter the following token into the field on "
                           "the HIT webpage, and close this browser window. ",
                "room": room_id,
                **kwargs,
            },
        )
        self.sio.emit(
            "text",
            {
                "message": f"Here is your token: {code}",
                "room": room_id,
                **kwargs
            },
        )
        return code

    def close_game(self, room_id):
        """Erase any data structures no longer necessary."""
        self.sio.emit(
            "text",
            {
                "message": "You will be moved out of this room "
                           f"in {TIME_CLOSE*2*60}-{TIME_CLOSE*3*60}s.",
                "room": room_id,
            },
        )
        sleep(2)
        self.sio.emit(
            "text",
            {
                "message": "Make sure to save your token before that.",
                "room": room_id
            },
        )
        sleep(TIME_CLOSE*2*60)
        self.room_to_read_only(room_id)

        # remove users from room
        for usr in self.players_per_room[room_id]:
            response = requests.get(
                f"{self.uri}/users/{usr['id']}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            self.request_feedback(response, "get user")
            etag = response.headers["ETag"]

            response = requests.delete(
                f"{self.uri}/users/{usr['id']}/rooms/{room_id}",
                headers={"If-Match": etag, "Authorization": f"Bearer {self.token}"},
            )
            self.request_feedback(response, "remove user from task room")

        # remove any task room specific objects
        self.players_per_room.pop(room_id)

    def room_to_read_only(self, room_id):
        """Set room to read only."""
        response = requests.patch(
            f"{self.uri}/rooms/{room_id}/attribute/id/text",
            json={"attribute": "readonly", "value": "True"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.request_feedback(response, "set room to read_only")

        response = requests.patch(
            f"{self.uri}/rooms/{room_id}/attribute/id/text",
            json={"attribute": "placeholder", "value": "This room is read-only"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.request_feedback(response, "inform user that room is read_only")


class APIChatBot(GenericChatbot):
    def register_callbacks(self):

        @self.sio.event
        def joined_room(data):
            """Triggered once after the bot joins a room."""
            room_id = data["room"]

            # read out task greeting
            # ask players to send /ready
            sleep(1)  # avoiding namespace errors
            self.sio.emit(
                "text",
                {
                    "message": TASK_GREETING,
                    "room": room_id,
                    "html": True
                }
            )
            sleep(0.5)

        @self.sio.event
        def status(data):
            """Triggered if a user enters or leaves a room."""
            # check whether the user is eligible to join this task
            task = requests.get(
                f"{self.uri}/users/{data['user']['id']}/task",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            self.request_feedback(task, "set task instruction title")
            if not task.json() or task.json()["id"] != int(self.task_id):
                return

        @self.sio.event
        def command(data):
            """Parse user commands.
            Two commands are covered here:
            - /ready starts the dialog
            - /stop stops the dialog. Dialogs also end after the maximum
                number of turns as defined in the Game
            """
            LOG.debug(
                f"Received a command from {data['user']['name']}: {data['command']}"
            )

            room_id = data["room"]
            user_id = data["user"]["id"]

            if data["command"].startswith("ready"):
                self._command_ready(room_id, user_id)
            elif data["command"].startswith("stop"):
                self.command_stop(room_id, user_id)
            else:
                self.sio.emit(
                    "text",
                    {
                        "message": "Sorry, but I do not understand this command.",
                        "room": room_id,
                        "receiver_id": user_id,
                    },
                )
