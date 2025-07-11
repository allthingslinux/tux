import random
from enum import Enum

from bot import Tux
from discord import app_commands
from discord.ext import commands
from ui.embeds import EmbedCreator
from utils.config import CONFIG
from utils.functions import docstring_parameter

linux_facts = [
    "The Linux kernel has over 36 million lines of code in its Git repository.",
    "The vast majority of the world's supercomputers run on Linux.",
    "Linux 1.0 was launched on September 17, 1991 featuring 176,250 lines of code.",
    "There's an easter egg in `apt` if you enter `apt moo`.",
    "Linus Torvalds was around 22 years old when he started work on the Linux Kernel in 1991. In the same year, he also released prototypes of the kernel publicly.",
    "Linux's 1.0 release was in March 1994.",
    "Less than 1% of the latest kernel release includes code written by Linus Torvalds.",
    "Approximately 13.3% of the latest Linux kernel is made up of blank lines.",
    "Vim has various easter eggs. A notable one is found by typing :help 42 into the command bar.",
    "Slackware is the oldest active linux distribution being released on the 17th July 1993.",
    "Freax was the original planned name for Linux.",
    "The first GUI that ran on Linux was X Window System. It ran on Linux Kernel version 0.95.",
    "The Linux Kernel was the first OS kernel to support x86-64 in 2001.",
    "Over 14,600 individual developers from over 1,300 different companies have contributed to the kernel.",
    "95% of the Linux kernel is written in the C programming Language. Assembly language is the second most used language for Linux at 2.8%.",
    "The first kernel version - Version 0.01 - contained about 10,000 lines of code.",
    "96.3% of the top 1,000,000 web servers were reported to run on Linux.",
    "In the early 2000s, Steve Jobs, who at the time was the CEO of Apple, offered a job to Linus Torvalds to work on OSX which Torvalds declined.",
    "Linus Torvalds said that he would have never created Linux if FreeBSD had been available at the time.",
    "Linux is used by every major space programme in the world including NASA, SpaceX, and the European Space Agency.",
]

cat_facts = [
    "Unlike dogs, cats do not have a sweet tooth. Scientists believe this is due to a mutation in a key taste receptor.",
    "When a cat chases its prey, it keeps its head level. Dogs and humans bob their heads up and down.",
    "The technical term for a cat's hairball is a “bezoar.”",
    "A group of cats is called a “clowder.”",
    "A cat can't climb head first down a tree because every claw on a cat's paw points the same way. To get down from a tree, a cat must back down.",
    "Cats make about 100 different sounds. Dogs make only about 10.",
    "Every year, nearly four million cats are eaten in Asia.",
    "There are more than 500 million domestic cats in the world, with approximately 40 recognized breeds.",
    "Approximately 24 cat skins can make a coat.",
    "While it is commonly thought that the ancient Egyptians were the first to domesticate cats, the oldest known pet cat was recently found in a 9,500-year-old grave on the Mediterranean island of Cyprus. This grave predates early Egyptian art depicting cats by 4,000 years or more.",
    "During the time of the Spanish Inquisition, Pope Innocent VIII condemned cats as evil and thousands of cats were burned. Unfortunately, the widespread killing of cats led to an explosion of the rat population, which exacerbated the effects of the Black Death.",
    "During the Middle Ages, cats were associated with witchcraft, and on St. John's Day, people all over Europe would stuff them into sacks and toss the cats into bonfires. On holy days, people celebrated by tossing cats from church towers.",
    "The first cat in space was a French cat named Felicette (a.k.a. “Astrocat”) In 1963, France blasted the cat into outer space. Electrodes implanted in her brains sent neurological signals back to Earth. She survived the trip.",
    "The group of words associated with cat (catt, cath, chat, katze) stem from the Latin catus, meaning domestic cat, as opposed to feles, or wild cat.",
    "The term “puss” is the root of the principal word for “cat” in the Romanian term pisica and the root of secondary words in Lithuanian (puz) and Low German puus. Some scholars suggest that “puss” could be imitative of the hissing sound used to get a cat's attention. As a slang word for the female pudenda, it could be associated with the connotation of a cat being soft, warm, and fuzzy.",
    "Approximately 40,000 people are bitten by cats in the U.S. annually.",
    "Cats are the world's most popular pets, outnumbering dogs by as many as three to one",
    "Cats are North America's most popular pets: there are 73 million cats compared to 63 million dogs. Over 30% of households in North America own a cat.",
    "According to Hebrew legend, Noah prayed to God for help protecting all the food he stored on the ark from being eaten by rats. In reply, God made the lion sneeze, and out popped a cat.",
    "A cat's hearing is better than a dog's. And a cat can hear high-frequency sounds up to two octaves higher than a human.",
    "A cat can travel at a top speed of approximately 31 mph (49 km) over a short distance.",
    "A cat rubs against people not only to be affectionate but also to mark out its territory with scent glands around its face. The tail area and paws also carry the cat's scent.",
    "Researchers are unsure exactly how a cat purrs. Most veterinarians believe that a cat purrs by vibrating vocal folds deep in the throat. To do this, a muscle in the larynx opens and closes the air passage about 25 times per second.",
    "When a family cat died in ancient Egypt, family members would mourn by shaving off their eyebrows. They also held elaborate funerals during which they drank wine and beat their breasts. The cat was embalmed with a sculpted wooden mask and the tiny mummy was placed in the family tomb or in a pet cemetery with tiny mummies of mice.",
    "In 1888, more than 300,000 mummified cats were found an Egyptian cemetery. They were stripped of their wrappings and carted off to be used by farmers in England and the U.S. for fertilizer.",
]

tux_facts = [
    f"As of 2025, {CONFIG.BOT_NAME} has over 20 thousand lines of code.",
    f"The first stable release of {CONFIG.BOT_NAME} was over 1 year after its creation.",
    f"{CONFIG.BOT_NAME} is fully open source and available on GitHub (https://github.com/allthingslinux/tux). Unless you forked it and made it private, in which case, please make it public (GPLv3).",
]

taco_bell_facts = [
    "It didn't start with tacos. Before Taco Bell, founder Glen Bell created fast-food joint Taco Tia, offering hamburgers, hot dogs, milkshakes and tacos. Seeing the success of the tacos, Bell eventually launched Taco Bell in 1962 in Downey, Calif.",
    "Originally, all menu items were only $0.19. In its early days in the 1960s, Taco Bell's menu only offered a limited number of classic options including tacos, burritos, frijoles and tostadas. Each item cost only $0.19.",
    "Taco Bell's original menu offered chiliburgers, alongside tacos and burritos. The chiliburgers were eventually taken off the menu.",
    "The first Taco Bell location featured fire pits and mariachi bands. It was an outdoor hangout with a walk-up window and no indoor seating.",
    "PepsiCo used to own Taco Bell. PepsiCo acquired Taco Bell in 1978 as part of its Yum! Brands portfolio until 1997.",
    "Taco Bell was the first fast food chain to hire women as managers, valuing diverse leadership early on.",
    "The Taco Bell Chihuahua Gidget also starred in the movie 'Legally Blonde 2' after popularizing the line 'Yo quiero Taco Bell' in commercials.",
    "Gidget lived like a star: she flew first class, opened the New York Stock Exchange, appeared at Madison Square Garden, and died in 2009 at 15 years old.",
    "Taco Bell's beef contains 88% beef and 12% 'secret recipe', after a lawsuit in 2011 claimed it was only 35% beef.",
    "Creedence Clearwater Revival ate there. A 1968 photo shows the band at Taco Bell, and Macaulay Culkin has also been spotted there.",
    "Taco Bell once 'purchased' the Liberty Bell as an April Fools' prank in 1996, later pledging $50,000 to its upkeep to appease protestors.",
    "An angry college football star got stuck in a Taco Bell drive-thru window in 1999 after trying to retrieve a missing chalupa.",
    "Free tacos were offered if a piece of the deorbiting Mir space station landed on a target in 2001. No fragment hit the target.",
    "Taco Bell was sued by rapper 50 Cent in 2008 for unauthorized use of his name and image during the 'Why Pay More?' campaign.",
    "Infomercial icon Billy Mays signed to be Taco Bell's spokesperson in 2009 but died of heart failure before filming.",
    "Taco Bell petitioned the Federal Reserve in 2010 to bring back $2 bills to promote its $2 menu; the petition gained attention but no action.",
    "Taco Bell no longer has a kids' menu since 2013, aiming its focus on millennials and rebranding as an edgy brand.",
    "The Doritos Locos Taco added 15,000 jobs in 2012 due to its popularity, helping Taco Bell outgrow Pizza Hut, KFC, and McDonald's.",
    "It took two years and 40 different recipes to create the Doritos Locos Taco, which sells nearly 1 million units per day.",
    "Taco Bell attempted an upscale spin-off, U.S. Taco Co., in 2014, but it closed after one year due to pricing, quality, and licensing issues.",
]


class FactType(Enum):
    LINUX = "Linux"
    TUX = f"{CONFIG.BOT_NAME}"
    CAT = "Cat"
    TACO_BELL = "Taco Bell"
    RANDOM = "Random"


# dictionary to map fact types to their respective lists
# TODO: add more facts and make some grabbed from apis
"""
https://uselessfacts.jsph.pl/
https://alexwohlbruck.github.io/cat-facts/
https://dukengn.github.io/Dog-facts-API/
https://kinduff.github.io/dog-api/
https://github.com/wh-iterabb-it/meowfacts
https://chandan-02.github.io/anime-facts-rest-api/
"""
fact_type_map = {
    FactType.LINUX: linux_facts,
    FactType.TUX: tux_facts,
    FactType.CAT: cat_facts,
    FactType.TACO_BELL: taco_bell_facts,
    FactType.RANDOM: linux_facts + tux_facts + cat_facts + taco_bell_facts,
}


class Fact(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @commands.hybrid_command(name="fact", aliases=["funfact"])
    @app_commands.describe(fact_type="Select the category of fact to retrieve")
    @app_commands.choices(fact_type=[app_commands.Choice(name=ft.value, value=ft.value) for ft in FactType])
    @docstring_parameter(
        f"Available categories: {', '.join([ft.value for ft in FactType])}. Default category is {FactType.RANDOM.value}.",
    )
    async def fact(self, ctx: commands.Context[Tux], *, fact_type: str = FactType.RANDOM.value) -> None:
        """
        Get a random fun fact from the specified category.

        {0}

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        fact_type : str
            The category of fact to retrieve. {0}
        """

        # Map selected name back to enum (case-insensitive)
        mapping = {ft.value.lower(): ft for ft in FactType}
        key = fact_type.lower()
        if key not in mapping:
            opts = ", ".join(ft.value for ft in FactType)
            await ctx.send(f"Invalid category '{fact_type}'. Available: {opts}.")
            return
        sel = mapping[key]
        # Pick a random fact
        facts = fact_type_map.get(sel, [])
        description = random.choice(facts) if facts else "No facts available for this category."

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title=f"Fun Fact ({sel.value})",
            description=description,
            custom_author_text="Click here to submit more facts!",
            custom_author_text_url="https://github.com/allthingslinux/tux/blob/main/tux/cogs/fun/fact.py",
            custom_author_icon_url="https://github.com/allthingslinux/tux/blob/main/assets/emojis/tux_info.png?raw=true",
        )

        # Send the fact embed
        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Fact(bot))
