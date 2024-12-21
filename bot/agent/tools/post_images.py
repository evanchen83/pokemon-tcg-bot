import asyncio

import discord
from langchain.tools import StructuredTool
from pydantic import BaseModel, HttpUrl
from reactionmenu import ViewButton, ViewMenu

from bot.agent import global_interaction


async def post_images(interaction: discord.Interaction, image_urls: list[str]):
    menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
    for image_url in image_urls:
        menu.add_page(
            discord.Embed().set_image(url=image_url).set_footer(text=image_url)
        )

    menu.add_button(ViewButton.back())
    menu.add_button(ViewButton.next())
    await menu.start()


def sync_post_images_caller(image_urls: list[str]):
    loop = asyncio.get_event_loop()
    loop.create_task(post_images(global_interaction.get_interaction(), image_urls))

    return "Successfully posted images to channel."


class ImageSchema(BaseModel):
    image_urls: list[HttpUrl]


post_images_tool = StructuredTool(
    func=sync_post_images_caller,
    name="post_images_tool",
    description=(
        "This tool handles posting image URLs in a channel or providing images based on a request. Use this tool "
        "when you encounter phrases like 'post the images in the channel', 'provide some images', or when another tool "
        "returns a response containing image URLs. This ensures that image URLs are properly handled and posted."
    ),
    args_schema=ImageSchema,
)
