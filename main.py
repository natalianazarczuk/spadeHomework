import asyncio
import random
import time
from datetime import datetime, timedelta
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State, PeriodicBehaviour
from spade.message import Message
from spade.template import Template

INITIAL_STATE = "initial"
DISTRACTED_STATE = "distracted"


class BehaviorFSM1(FSMBehaviour):
    async def on_start(self):
        print(f"[1]FSM starting at state {self.current_state}")

    async def on_end(self):
        print(f"[1]FSM finished at state {self.current_state}")
        await self.agent.stop()


class BehaviorFSM2(FSMBehaviour):
    async def on_start(self):
        print(f"[2]FSM starting at initial state {self.current_state}")

    async def on_end(self):
        print(f"[2]FSM finished at state {self.current_state}")
        await self.agent.stop()


class StateOne(State):
    def __init__(self):
        super().__init__()
        self.counter = 1

    async def run(self):
        msg = await self.receive(timeout=5)
        if not msg:
            print(f"[1]Counter: {self.counter}")
            msg = Message(to="nnagent2@hot-chilli.eu")
            msg.set_metadata("performative", "query")
            msg.body = str(self.counter)
            await self.send(msg)
            print(f"[1]Message sent {msg.body}")
            self.set_next_state(INITIAL_STATE)
        if str(msg.sender) == "nnagent3@hot-chilli.eu":
            print(f"[1]Received message from Agent 3: {msg.body}")
            if random.random() < 0.4:
                msg.to = "nnagent2@hot-chilli.eu"
                msg.sender = "nnagent1@hot-chilli.eu"
                await self.send(msg)
                print(f"[1]Message sent {msg.body}")
                self.set_next_state(DISTRACTED_STATE)
        elif str(msg.sender) == "nnagent2@hot-chilli.eu":
            print(f"[1]Received message from Agent 2: {msg.body}")
            self.counter = int(msg.body) + 1
            print(f"[1]Counter: {self.counter}")
            msg = Message(to="nnagent2@hot-chilli.eu")
            msg.set_metadata("performative", "query")
            msg.body = str(self.counter)
            await self.send(msg)
            print(f"[1]Message sent {msg.body}")
            self.set_next_state(INITIAL_STATE)
        await asyncio.sleep(1)


class StateTwo(State):
    async def run(self):
        print("I'm at the distracted state")
        await self.agent.stop()


class StateThree(State):
    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            print("[2]Did not received any message after 10 seconds")
        elif str(msg.sender) == "nnagent3@hot-chilli.eu":
            print(f"[2]Received message from Agent 3: {msg.body}")
            if random.random() < 0.3:
                msg.to = "nnagent1@hot-chilli.eu"
                msg.sender = "nnagent2@hot-chilli.eu"
                await self.send(msg)
                print(f"[2]Message sent: {msg.body}")
                self.set_next_state(DISTRACTED_STATE)
        elif str(msg.sender) == "nnagent1@hot-chilli.eu":
            print(f"[2]Received message from Agent 1: {msg.body}")
            self.counter = int(msg.body) + 1
            self.set_next_state(INITIAL_STATE)
            print(f"[2]Counter: {self.counter}")
            msg = Message(to="nnagent1@hot-chilli.eu")
            msg.set_metadata("performative", "query")
            msg.body = str(self.counter)
            await self.send(msg)
            print(f"[2]Message sent {msg.body}")
        await asyncio.sleep(1)


class Agent1(Agent):
    async def setup(self):
        print("Agent 1 starting . . .")
        fsm = BehaviorFSM1()
        fsm.add_state(name=INITIAL_STATE, state=StateOne(), initial=True)
        fsm.add_state(name=DISTRACTED_STATE, state=StateTwo())
        fsm.add_transition(source=INITIAL_STATE, dest=INITIAL_STATE)
        fsm.add_transition(source=INITIAL_STATE, dest=DISTRACTED_STATE)
        template = Template()
        template.set_metadata("performative", "query")
        self.add_behaviour(fsm, template)


class Agent2(Agent):
    async def setup(self):
        print("Agent 2 starting . . .")
        fsm = BehaviorFSM2()
        fsm.add_state(name=INITIAL_STATE, state=StateThree(), initial=True)
        fsm.add_state(name=DISTRACTED_STATE, state=StateTwo())
        fsm.add_transition(source=INITIAL_STATE, dest=INITIAL_STATE)
        fsm.add_transition(source=INITIAL_STATE, dest=DISTRACTED_STATE)
        template = Template()
        template.set_metadata("performative", "query")
        self.add_behaviour(fsm, template)


class Agent3(Agent):
    class InterruptBehavior(PeriodicBehaviour):
        async def run(self):
            print(f"[3]Interrupting Behavior started at {datetime.now().time()}: ")
            if random.random() < 0.5:
                receiver = "nnagent1@hot-chilli.eu"
            else:
                receiver = "nnagent2@hot-chilli.eu"

            msg = Message(to=receiver)
            msg.set_metadata("performative", "query")
            msg.body = str(random.randint(1, 20))

            await self.send(msg)
            print(f"[3]Message sent {msg.body}")

        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        print("Agent 3 starting . . .")
        start_at = datetime.now() + timedelta(seconds=10)
        i = self.InterruptBehavior(period=10, start_at=start_at)
        self.add_behaviour(i)


if __name__ == "__main__":
    a1 = Agent1("nnagent1@hot-chilli.eu", "123")
    a2 = Agent2("nnagent2@hot-chilli.eu", "123")
    a3 = Agent3("nnagent3@hot-chilli.eu", "123")

    first = a1.start()
    second = a2.start()
    third = a3.start()
    time.sleep(1)
    first.result()
    second.result()
    third.result()

    while a1.is_alive() & a2.is_alive() & a3.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            a1.stop()
            a2.stop()
            a3.stop()
            break
    print("Agent finished")
