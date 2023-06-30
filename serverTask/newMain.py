import socket
import sys
import time
import threading

MAX_CONNECTIONS = 20
TIMEOUT_RECHARGING = 5

serverKey = [23019, 32037, 18789, 16443, 18189]
clientKey = [32037, 29295, 13603, 29533, 21952]


def run_server(port=9090):
    serv_sock = create_serv_sock(port)

    cid = 0
    try:
        while True:
            client_sock = accept_client_conn(serv_sock, cid)
            t = threading.Thread(target=serve_client,
                                 args=(client_sock, cid))
            t.start()
            cid += 1
    except KeyboardInterrupt:
        serv_sock.close()
        print("Server stopped! Thank you for using!")


def findHash(name, key):
    return ((sum(name) * 1000 % 65536) + key) % 65536


def serve_client(client_sock, cid):
    if not authentication(client_sock, cid):
        sock_close(client_sock, cid)
        return

    if not movement(client_sock, cid):
        sock_close(client_sock, cid)
        return

    sock_close(client_sock, cid)


def authentication(client_sock, cid):
    maxLen = 20
    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return False

    name = request[0:len(request) - 2]

    response = "107 KEY REQUEST\a\b"
    write_response(client_sock, bytes(response, 'utf-8'))

    maxLen = 5
    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return False
    try:
        keyId = int(request.decode()[0:len(request) - 2])

        if keyId > 4 or keyId < 0:
            response = "303 KEY OUT OF RANGE\a\b"
            write_response(client_sock, bytes(response, 'utf-8'))

            return False
    except ValueError:
        response = "301 SYNTAX ERROR\a\b"
        write_response(client_sock, bytes(response, 'utf-8'))
        return False

    servHash = findHash(name, serverKey[keyId])
    response = str(servHash) + '\a' + '\b'
    write_response(client_sock, bytes(response, 'utf-8'))

    maxLen = 7
    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return False
    elif request.decode()[len(request) - 3] == ' ':
        response = "301 SYNTAX ERROR\a\b"
        write_response(client_sock, bytes(response, 'utf-8'))
        return False
    try:
        clientHash = int(request.decode()[0:len(request) - 2])
    except ValueError:
        response = "301 SYNTAX ERROR\a\b"
        write_response(client_sock, bytes(response, 'utf-8'))
        return False

    countedClientHash = findHash(name, clientKey[keyId])
    if clientHash == countedClientHash:
        response = "200 OK" + '\a' + '\b'
        write_response(client_sock, bytes(response, 'utf-8'))
    else:
        response = "300 LOGIN FAILED" + '\a' + '\b'
        write_response(client_sock, bytes(response, 'utf-8'))
        return False

    return True


def getCoordinates(message, client_sock):
    num = ""
    coordinates = []

    for i in range(3, len(message)):
        if message[i] != ' ':
            num = num + message[i]
        else:
            try:
                coordinates.append(int(num))
            except ValueError:
                response = "301 SYNTAX ERROR\a\b"
                write_response(client_sock, bytes(response, 'utf-8'))
                client_sock.close()
                sys.exit()

            num = ""

    try:
        coordinates.append(int(num))
    except ValueError:
        response = "301 SYNTAX ERROR\a\b"
        write_response(client_sock, bytes(response, 'utf-8'))
        client_sock.close()
        sys.exit()

    if len(coordinates) != 2:
        response = "301 SYNTAX ERROR\a\b"
        write_response(client_sock, bytes(response, 'utf-8'))
        client_sock.close()
        sys.exit()

    return coordinates


def findDirect(fCoordinates, sCoordinates):
    if sCoordinates[1] - fCoordinates[1] == 0:
        if sCoordinates[0] - fCoordinates[0] > 0:
            direct = "right"
        else:
            direct = "left"
    elif sCoordinates[1] - fCoordinates[1] > 0:
        direct = "up"
    else:
        direct = "down"

    return direct


def moves(client_sock, request, fCoordinates, sCoordinates, cid):
    direct = findDirect(fCoordinates, sCoordinates)

    currCoordinates = []
    maxLen = 12

    if sCoordinates[1] != 0:
        match direct:
            case "right":
                if sCoordinates[1] > 0:
                    message = "104 TURN RIGHT\a\b"
                    write_response(client_sock, bytes(message, 'utf-8'))

                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []
                else:
                    message = "103 TURN LEFT\a\b"
                    write_response(client_sock, bytes(message, 'utf-8'))

                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []
            case "left":
                if sCoordinates[1] > 0:
                    message = "103 TURN LEFT\a\b"
                    write_response(client_sock, bytes(message, 'utf-8'))

                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []
                else:
                    message = "104 TURN RIGHT\a\b"
                    write_response(client_sock, bytes(message, 'utf-8'))

                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []
            case "down":
                if sCoordinates[1] < 0:
                    message = "103 TURN LEFT\a\b"
                    write_response(client_sock, bytes(message, 'utf-8'))

                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []
                    getCoordinates(request.decode()[0:len(request) - 2], client_sock)

                    message = "103 TURN LEFT\a\b"
                    write_response(client_sock, bytes(message, 'utf-8'))

                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []

            case "up":
                if sCoordinates[1] > 0:
                    message = "103 TURN LEFT\a\b"
                    write_response(client_sock, bytes(message, 'utf-8'))

                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []
                    getCoordinates(request.decode()[0:len(request) - 2], client_sock)

                    message = "103 TURN LEFT\a\b"
                    write_response(client_sock, bytes(message, 'utf-8'))

                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []

        currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)
        prevCoordinates = []
        flag = True
        while currCoordinates[1] != 0:
            message = "102 MOVE\a\b"
            write_response(client_sock, bytes(message, 'utf-8'))

            prevCoordinates = currCoordinates

            request = read_request(client_sock, cid, maxLen)
            if request is None:
                return []
            currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

            if currCoordinates[0] == prevCoordinates[0] and currCoordinates[1] == prevCoordinates[1]:
                currCoordinates = newDetour(client_sock, cid, flag)
                flag = not flag

        if currCoordinates[0] != 0:

            if currCoordinates[0] > 0:
                if sCoordinates[1] > 0:
                    message = "104 TURN RIGHT\a\b"
                else:
                    message = "103 TURN LEFT\a\b"
            else:
                if sCoordinates[1] > 0:
                    message = "103 TURN LEFT\a\b"
                else:
                    message = "104 TURN RIGHT\a\b"

            write_response(client_sock, bytes(message, 'utf-8'))

            request = read_request(client_sock, cid, maxLen)
            if request is None:
                return []
            currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

            flag = True
            while currCoordinates[0] != 0:
                message = "102 MOVE\a\b"
                write_response(client_sock, bytes(message, 'utf-8'))

                prevCoordinates = currCoordinates

                request = read_request(client_sock, cid, maxLen)
                if request is None:
                    return []
                currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

                if currCoordinates[0] == prevCoordinates[0] and currCoordinates[1] == prevCoordinates[1]:
                    currCoordinates = newDetour(client_sock, cid, flag)
                    flag = not flag

    else:
        if sCoordinates[0] != 0:
            match direct:
                case "up":
                    if sCoordinates[0] > 0:
                        message = "103 TURN LEFT\a\b"
                    else:
                        message = "104 TURN RIGHT\a\b"

                    write_response(client_sock, bytes(message, 'utf-8'))
                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []
                case "down":
                    if sCoordinates[0] > 0:
                        message = "104 TURN RIGHT\a\b"
                    else:
                        message = "103 TURN LEFT\a\b"

                    write_response(client_sock, bytes(message, 'utf-8'))
                    request = read_request(client_sock, cid, maxLen)
                    if request is None:
                        return []
                case "right":
                    if sCoordinates[0] > 0:
                        message = "103 TURN LEFT\a\b"
                        write_response(client_sock, bytes(message, 'utf-8'))

                        request = read_request(client_sock, cid, maxLen)
                        if request is None:
                            return []
                        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

                        message = "103 TURN LEFT\a\b"
                        write_response(client_sock, bytes(message, 'utf-8'))

                        request = read_request(client_sock, cid, maxLen)
                        if request is None:
                            return []
                case "left":
                    if sCoordinates[0] < 0:
                        message = "103 TURN LEFT\a\b"
                        write_response(client_sock, bytes(message, 'utf-8'))

                        request = read_request(client_sock, cid, maxLen)
                        if request is None:
                            return []
                        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

                        message = "103 TURN LEFT\a\b"
                        write_response(client_sock, bytes(message, 'utf-8'))

                        request = read_request(client_sock, cid, maxLen)
                        if request is None:
                            return []

            currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)
            prevCoordinates = []
            flag = True
            while currCoordinates[0] != 0:
                message = "102 MOVE\a\b"
                write_response(client_sock, bytes(message, 'utf-8'))

                prevCoordinates = currCoordinates

                request = read_request(client_sock, cid, maxLen)
                if request is None:
                    return []
                currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

                if currCoordinates[0] == prevCoordinates[0] and currCoordinates[1] == prevCoordinates[1]:
                    currCoordinates = newDetour(client_sock, cid, flag)
                    flag = not flag

    if currCoordinates[0] == 0 and currCoordinates[1] == 1 or currCoordinates[0] == 0 and currCoordinates[1] == -1:
        message = "103 TURN LEFT\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

        message = "102 MOVE\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    return currCoordinates

def newDetour(client_sock, cid, flag):
    maxLen = 12

    if flag:
        message = "104 TURN RIGHT\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

        message = "102 MOVE\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

        message = "103 TURN LEFT\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)
    else:
        message = "103 TURN LEFT\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

        message = "102 MOVE\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

        message = "104 TURN RIGHT\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    return currCoordinates


def detour(client_sock, cid):
    message = "104 TURN RIGHT\a\b"
    write_response(client_sock, bytes(message, 'utf-8'))

    maxLen = 12

    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return []
    getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    message = "102 MOVE\a\b"
    write_response(client_sock, bytes(message, 'utf-8'))

    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return []
    getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    message = "103 TURN LEFT\a\b"
    write_response(client_sock, bytes(message, 'utf-8'))

    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return []
    getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    message = "102 MOVE\a\b"
    write_response(client_sock, bytes(message, 'utf-8'))

    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return []
    currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    if currCoordinates[1] != 0:
        message = "102 MOVE\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []

        message = "103 TURN LEFT\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

        message = "102 MOVE\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        getCoordinates(request.decode()[0:len(request) - 2], client_sock)

        message = "104 TURN RIGHT\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return []
        currCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    return currCoordinates


def movement(client_sock, cid):
    message = "102 MOVE\a\b"
    write_response(client_sock, bytes(message, 'utf-8'))

    maxLen = 12

    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return False
    fCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    message = "102 MOVE\a\b"
    write_response(client_sock, bytes(message, 'utf-8'))

    request = read_request(client_sock, cid, maxLen)
    if request is None:
        return False
    sCoordinates = getCoordinates(request.decode()[0:len(request) - 2], client_sock)

    if sCoordinates[0] == fCoordinates[0] and sCoordinates[1] == fCoordinates[1]:
        fCoordinates = sCoordinates
        sCoordinates = detour(client_sock, cid)

    currCoordinates = []

    if sCoordinates[0] == 0 and sCoordinates[1] == 0:
        currCoordinates.append(0)
        currCoordinates.append(0)
    else:
        currCoordinates = moves(client_sock, request, fCoordinates, sCoordinates, cid)
    if not currCoordinates:
        return False
    elif currCoordinates[0] == 0 and currCoordinates[1] == 0:
        message = "105 GET MESSAGE\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

        maxLen = 100
        request = read_request(client_sock, cid, maxLen)
        if request is None:
            return False

        message = "106 LOGOUT\a\b"
        write_response(client_sock, bytes(message, 'utf-8'))

    return True


def create_serv_sock(serv_port):
    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv_sock.bind(('', serv_port))
    serv_sock.listen(MAX_CONNECTIONS)
    return serv_sock


def accept_client_conn(serv_sock, cid):
    client_sock, client_addr = serv_sock.accept()
    print(f'Client #{cid} connected '
          f'{client_addr[0]}:{client_addr[1]}')
    return client_sock


def read_request(client_sock, cid, maxLen):
    delimiters = [7, 8]

    request = bytearray()

    try:
        while True:

            client_sock.settimeout(1)
            try:
                chunk = client_sock.recv(1)
            except TimeoutError:
                sock_close(client_sock, cid)
                sys.exit()

            request += chunk

            if len(request) >= 2:
                if len(request.decode()) >= maxLen and not request.decode() in "RECHARGING\a\b" and not ((delimiters[0] == request[-2]) and (delimiters[1] == request[-1])):
                    response = "301 SYNTAX ERROR\a\b"
                    write_response(client_sock, bytes(response, 'utf-8'))
                    sock_close(client_sock, cid)
                    sys.exit()
                elif (delimiters[0] == request[-2]) and (delimiters[1] == request[-1]):

                    if request.decode() == "RECHARGING\a\b":
                        request.clear()
                        client_sock.settimeout(5)
                        try:
                            chunk = client_sock.recv(12)

                            if chunk == b'FULL POWER\a\b':
                                continue
                            else:
                                response = "302 LOGIC ERROR\a\b"
                                write_response(client_sock, bytes(response, 'utf-8'))
                                return None

                        except TimeoutError:
                            return None
                    elif request.decode() == "FULL POWER\a\b":
                        request.clear()
                        response = "302 LOGIC ERROR\a\b	"
                        write_response(client_sock, bytes(response, 'utf-8'))
                        return None

                    return request

    except ConnectionResetError:
        return None


def sock_close(client_sock, cid):
    client_sock.close()
    print(f'Client #{cid} has been served')


def write_response(client_sock, response):
    client_sock.sendall(response)


if __name__ == '__main__':
    run_server()
