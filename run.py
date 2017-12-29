from alexis import Alexis

if __name__ == '__main__':
    ale = Alexis()
    ale.init()
    ale.http_session.close()
