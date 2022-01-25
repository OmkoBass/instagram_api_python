from os import path
from instaloader import Profile, ProfileNotExistsException, LoginRequiredException
from .constants import PAGE_SIZE


def search_profile(context, username):
    try:
        profile = Profile.from_username(context, username)
    except ProfileNotExistsException as err:
        return [str(err), 404]
    except LoginRequiredException as err:
        return [str(err), 401]

    return profile


def try_load_session(instaloader, user):
    # Just try to load the session,
    # It's not important if it fails
    # Because everyone can access
    if user:
        try:
            # I want to go one dir up,
            # That's why i called path.dirname two times
            instaloader.load_session_from_file(
                user, f"{path.dirname(path.dirname(__file__))}/sessions/{user}"
            )
            return True

        except FileNotFoundError:
            return False


def get_all_stories(generator_stories):
    # Get the story for a specific user
    stories = []
    for story in generator_stories:
        for item in story.get_items():
            single_story = {}

            single_story["image"] = item.url
            if item.is_video:
                single_story["url"] = item.video_url
            else:
                single_story["url"] = item.url
            stories.append(single_story)

    return stories


def get_posts(generator_posts, page_number):
    # Get the posts for a specific user
    # get_highlight_stories_single explain the logic
    count = 0
    skip = (page_number - 1) * PAGE_SIZE
    limit = page_number * PAGE_SIZE

    posts = []

    if skip > generator_posts.count:
        return []

    for post in generator_posts:
        if count >= skip and count <= limit:
            single_post = {}

            single_post["image"] = post.url
            if post.is_video:
                single_post["url"] = post.video_url
            else:
                single_post["url"] = post.url
            posts.append(single_post)
        if count > limit:
            break

        count += 1

    return posts


def get_all_highlights(generator_highlights):
    highlights = []

    for highlight in generator_highlights:
        single_highlight = {}

        single_highlight['id'] = highlight.unique_id
        single_highlight['title'] = highlight.title
        single_highlight['url'] = highlight.cover_cropped_url
        highlights.append(single_highlight)

    return highlights


def get_highlight_stories_single(generator_highlights, highlight_id, page_number):
    count = 0
    skip = (page_number - 1) * PAGE_SIZE
    limit = page_number * PAGE_SIZE

    stories = []

    # For each highlight for a profile
    for highlight in generator_highlights:
        # If the highlight id matches the searched one
        if highlight.unique_id == highlight_id:
            # If we have nothing to get with that
            # page number then just return
            # 9 posts, 2 page number means a skip
            if skip > highlight.itemcount:
                return []
            # Get all the stories in the highlight
            for item in highlight.get_items():
                # Skip the ones you don't need
                if count >= skip and count <= limit:
                    single_story = {}

                    single_story["image"] = item.url
                    if item.is_video:
                        single_story["url"] = item.video_url
                    else:
                        single_story["url"] = item.url
                    stories.append(single_story)
                if count > limit:
                    break

                count += 1

    return stories
