import logging

import telegram.constants as constants
from revChatGPT.revChatGPT import Chatbot as ChatGPT3Bot

from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters


class ChatGPT3TelegramBot:
    """
    Class representing a Chat-GPT3 Telegram Bot.
    """
    def __init__(self, config: dict, gpt3_bot: ChatGPT3Bot):
        """
        Initializes the bot with the given configuration and GPT-3 bot object.
        :param config: A dictionary containing the bot configuration
        :param gpt3_bot: The GPT-3 bot object
        """
        self.config = config
        self.gpt3_bot = gpt3_bot
        self.disallowed_message = "Sorry, you are not allowed to use this bot. You can check out the source code at " \
                                  "https://github.com/n3d1117/chatgpt-telegram-bot"

    def help(self, update: Update, context: CallbackContext):
        """
        Shows the help menu.
        """
        update.message.reply_text("/start - Start the bot\n"
                                  "/reset - Reset conversation\n"
                                  "/help - Help menu\n\n"
                                  "Open source at https://github.com/n3d1117/chatgpt-telegram-bot",
                                  disable_web_page_preview=True)

    def start(self, update: Update, context: CallbackContext):
        """
        Handles the /start command.
        """
        if not self.is_allowed(update):
            logging.info(f'User {update.message.from_user.name} is not allowed to start the bot')
            self.send_disallowed_message(update, context)
            return

        logging.info('Bot started')
        context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a Chat-GPT3 Bot, please talk to me!")

    def reset(self, update: Update, context: CallbackContext):
        """
        Resets the conversation.
        """
        if not self.is_allowed(update):
            logging.info(f'User {update.message.from_user.name} is not allowed to reset the bot')
            self.send_disallowed_message(update, context)
            return

        logging.info('Resetting the conversation...')
        self.gpt3_bot.reset_chat()
        context.bot.send_message(chat_id=update.effective_chat.id, text="Done!")

    def prompt(self, update: Update, context: CallbackContext):
        """
        React to incoming messages and respond accordingly.
        """
        if not self.is_allowed(update):
            logging.info(f'User {update.message.from_user.name} is not allowed to use the bot')
            self.send_disallowed_message(update, context)
            return

        logging.info(f'New message received from user {update.message.from_user.name}')

        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.CHATACTION_TYPING)
        response = self.get_chatgpt_response(update.message.text)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=response['message'],
            parse_mode=constants.PARSEMODE_MARKDOWN
        )

    def get_chatgpt_response(self, message) -> dict:
        """
        Gets the response from the ChatGPT APIs.
        """
        try:
            response = self.gpt3_bot.get_chat_response(message)
            return response
        except Exception as e:
            logging.info(f'Error while getting the response: {str(e)}')
            return {"message": "I'm having some trouble talking to you, please try again later."}

    def send_disallowed_message(self, update: Update, context: CallbackContext):
        """
        Sends the disallowed message to the user.
        """
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.disallowed_message,
            disable_web_page_preview=True
        )

    def is_allowed(self, update: Update) -> bool:
        """
        Checks if the user is allowed to use the bot.
        """
        if self.config['allowed_user_ids'] == '*':
            return True
        return str(update.message.from_user.id) in self.config['allowed_user_ids'].split(',')

    def run(self):
        """
        Runs the bot indefinitely until the user presses Ctrl+C
        """
        updater = Updater(token=self.config['token'])
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler('start', self.start))
        dispatcher.add_handler(CommandHandler('reset', self.reset))
        dispatcher.add_handler(CommandHandler('help', self.help))
        dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), self.prompt))

        updater.start_polling()
        updater.idle()
