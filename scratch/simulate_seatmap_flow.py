import asyncio

from apps.bot.handlers import handle_view_chart


class User:
    id = 7667243487


class FakeMessage:
    def __init__(self):
        self.edits = []
        self.photos = []
        self.deleted = False

    async def edit_text(self, text, **kwargs):
        self.edits.append((text, kwargs))
        print("FAKE_EDIT", text.replace("\n", " | ")[:600])
        print("FAKE_MARKUP", kwargs.get("reply_markup"))

    async def answer(self, text, **kwargs):
        self.edits.append((text, kwargs))
        print("FAKE_ANSWER", text.replace("\n", " | ")[:600])

    async def answer_photo(self, photo, caption=None, **kwargs):
        self.photos.append((photo, caption, kwargs))
        print("FAKE_PHOTO", photo, (caption or "").replace("\n", " | ")[:600])

    async def delete(self):
        self.deleted = True
        print("FAKE_DELETE")


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.from_user = User()
        self.message = FakeMessage()

    async def answer(self, text=None, **kwargs):
        print("FAKE_CALLBACK_ANSWER", text)


async def main():
    for data in ["v_ch:6", "v_ch:1"]:
        print("CASE_BEGIN", data)
        callback = FakeCallback(data)
        await handle_view_chart(callback)
        print("CASE_END", data, "edits=", len(callback.message.edits), "photos=", len(callback.message.photos))


if __name__ == "__main__":
    asyncio.run(main())
