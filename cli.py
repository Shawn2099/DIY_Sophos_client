import argparse

from sophos_client.client import main
from sophos_client.doctor import run_doctor


def parse_args():
	parser = argparse.ArgumentParser(
		description="Sophos captive-portal WiFi client",
	)
	parser.add_argument(
		"-c",
		"--config",
		help="Path to YAML config file",
	)
	parser.add_argument(
		"--doctor",
		action="store_true",
		help="Run preflight diagnostics and exit",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = parse_args()
	if args.doctor:
		raise SystemExit(0 if run_doctor(config_path=args.config) else 1)
	main(config_path=args.config)