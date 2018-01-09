from alexis import Alexis

if __name__ == '__main__':
    ale = None

    try:
        ale = Alexis()
        ale.init()
    finally:
        ale.close()
