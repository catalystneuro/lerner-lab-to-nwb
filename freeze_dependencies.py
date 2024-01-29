import os


def main():
    os.system("pip freeze --exclude lerner-lab-to-nwb > frozen_dependencies.txt")


if __name__ == "__main__":
    main()
