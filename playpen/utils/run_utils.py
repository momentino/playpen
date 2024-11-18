import argparse

def read_gen_args(args: argparse.Namespace):
    return dict(temperature=args.temperature, max_tokens=args.max_tokens)