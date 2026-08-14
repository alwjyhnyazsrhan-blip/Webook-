import asyncio

from apps.bot.handlers import handle_book_event, handle_event_detail


class User:
    id = 7667243487


class FakeMarkup:
    pass


class FakeMessage:
    def __init__(self):
        self.edits = []
        self.photos = []
        self.deleted = False

    async def edit_text(self, text, **kwargs):
        self.edits.append((text, kwargs))
        print("FAKE_EDIT", text.replace("\n", " | ")[:500])

    async def answer(self, text, **kwargs):
        self.edits.append((text, kwargs))
        print("FAKE_ANSWER", text.replace("\n", " | ")[:500])

    async def answer_photo(self, photo, caption=None, **kwargs):
        self.photos.append((photo, caption, kwargs))
        print("FAKE_PHOTO", bool(photo), (caption or "").replace("\n", " | ")[:500])

    async def delete(self):
        self.deleted = True
        print("FAKE_DELETE")


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.from_user = User()
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, **kwargs):
        self.answers.append((text, kwargs))
        print("FAKE_CALLBACK_ANSWER", text)


class FakeState:
    def __init__(self):
        self.data = {}
        self.state = None

    async def update_data(self, **kwargs):
        self.data.update(kwargs)
        print("FAKE_STATE_DATA", self.data)

    async def clear(self):
        self.data = {}
        self.state = None
        print("FAKE_STATE_CLEAR")

    async def set_state(self, state):
        self.state = state
        print("FAKE_STATE_SET", state)

    async def get_data(self):
        return dict(self.data)


async def run_case(label, handler, data):
    print("CASE_BEGIN", label, data)
    callback = FakeCallback(data)
    state = FakeState()
    await handler(callback, state)
    print("CASE_END", label, "edits=", len(callback.message.edits), "photos=", len(callback.message.photos), "state=", state.state, "data=", state.data)


async def main():
    await run_case("broken_red_detail_neom_ettifa", handle_event_detail, "e_det:6")
    await run_case("contentful_helicopter_detail", handle_event_detail, "e_det:623")
    await run_case("sports_team_flow_neom_ettifa", handle_book_event, "b_ev:6")


if __name__ == "__main__":
    asyncio.run(main())
