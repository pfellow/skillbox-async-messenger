"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                temp = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == temp:
                        self.transport.write(
                            f"Логин {temp} занят, попробуйте другой".encode()
                        )
                        self.connection_lost(None)
                        break
                else:
                    self.login = temp
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history()
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.write_history(encoded)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")

    def send_history(self):
        self.transport.write("Последние сообщения:\n".encode())
        if len(self.server.messages) == 0:
            self.transport.write("Отсутствуют".encode())
        elif len(self.server.messages) < 10:
            for message in self.server.messages:
                self.transport.write(message + "\n".encode())
        else:
            for i in range(-10, 0):
                self.transport.write(self.server.messages[i] + "\n".encode())


class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    def write_history(self, message):
        self.messages.append(message)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
