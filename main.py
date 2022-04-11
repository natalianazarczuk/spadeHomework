import asyncio
import time
from spade.agent import Agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour
from spade.template import Template


class Agent1(Agent):
    class Behavior1(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.counter = 0

        async def run(self):
            self.counter += 1
            print("[1]Counter: {}".format(self.counter))
            msg = Message(to="nnagent2@hot-chilli.eu")     # Instantiate the message
            msg.set_metadata("performative", "query")  # Set the "inform" FIPA performative
            msg.body = str(self.counter)                  # Set the message content

            await self.send(msg)
            print("[1]Message sent!")

            print("[1]Waiting to receive")
            msg = await self.receive(timeout=20)
            if msg:
                print("[1]Message received with content: {}".format(msg.body))
            else:
                print("[1]Did not received any message after 20 seconds")

            self.counter = int(msg.body)
            await asyncio.sleep(1)


    async def setup(self):
        print("Agent 1 starting . . .")
        c = self.Behavior1()
        template = Template()
        template.set_metadata("performative", "query")
        self.add_behaviour(c, template)


class Agent2(Agent):
    class Behavior2(CyclicBehaviour):
        async def run(self):
            print("[2]Waiting to receive")

            msg = await self.receive(timeout=20)
            if msg:
                print("[2]Message received with content: {}".format(msg.body))
            else:
                print("[2]Did not received any message after 20 seconds")

            self.counter = int(msg.body) + 1

            print("[2]Counter: {}".format(self.counter))
            msg = Message(to="nnagent1@hot-chilli.eu")  # Instantiate the message
            msg.set_metadata("performative", "query")  # Set the "inform" FIPA performative
            msg.body = str(self.counter)  # Set the message content

            await self.send(msg)
            print("[2]Message sent!")
            await asyncio.sleep(1)

    async def setup(self):
        print("Agent 2 starting . . .")
        c = self.Behavior2()
        template = Template()
        template.set_metadata("performative", "query")
        self.add_behaviour(c, template)


if __name__ == "__main__":
    a1 = Agent1("nnagent1@hot-chilli.eu", "123")
    a2 = Agent2("nnagent2@hot-chilli.eu", "123")

    future = a1.start()
    idk = a2.start()
    future.result()
    idk.result()

    while a1.is_alive() & a2.is_alive():
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            a1.stop()
            a2.stop()
            break
    print("Agents finished")