#!/usr/bin/env python
"""Process an email inbox to do a correpsonding action with each message."""
import ConfigParser
import email
import imaplib
import logging
import optparse
import os
import re
import shutil
import sys
import textwrap
import time
from Logging import logger
from Processors import TransactionProcessor

class Powl:
    """Class for processing emails to do a corresponding action."""
    
    default_mailbox = 'inbox'
    file_config = 'config.cfg'

    # Email Processing
    def process_inbox(self):
        """Parse through an inbox of emails."""
        self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
        self.imap.login(self.address, self.password)
        self.imap.select(self.mailbox)
        search_response, email_ids = self.imap.search(None, "(Unseen)")
        self.log.info("PROCESSING INBOX")
        for email_id in email_ids[0].split():
            fetch_response, data = self.imap.fetch(email_id, "(RFC822)")
            mail = email.message_from_string(data[0][1])
            date = email.utils.parsedate(mail['Date'])
            for part in mail.walk():
                if part.get_content_type() == 'text/html':
                    body = part.get_payload()
                    message = self.strip_message_markup(body)
                    self.log.debug('EMAIL   %s', message.strip())
                    self.parse_message(message, date)

    def strip_message_markup(self, message):
        """Return message striped of markup."""
        retval = message
        retval = retval.replace('<P>','')
        retval = retval.replace('</P>','')
        retval = retval.replace('=0A',' ')
        retval = retval.replace('&amp;','&')
        return retval

    def parse_message(self, message, date):
        """Parse a message and determine its specified action."""
        # TODO: parse date from email
        action, data = message.split(' ',1)
        if action == 'transaction':
            self.process_transaction(data, date)
        elif action == 'todo':
            self.process_todo(data, date)
        else:
            self.process_miscellaneous(data, date)

    # Action Processing
    def process_miscellaneous(self, data, date):
        """Write miscellaneous message to file."""
        filename = self.path_miscellaneous + os.sep + 'miscellaneous.txt'
        file = open(filename, 'a')
        file.write(data)
        file.close()
        self.log.info('MISC\t%s', data)

    def process_todo(self, task, date):
        """Send task to toodledo."""
        pass
        
    def process_transaction(self, params, date):
        """Separate transaction data to pass onto processing."""
        params = re.split(' -', params)
        for param in params:
            param = param.strip()
            if re.match('d', param):
                debit = param.replace('d ','')
            elif re.match('c', param):
                credit = param.replace('c ','')
            elif re.match('a', param):
                amount = param.replace('a ','')
            elif re.match('m', param):
                memo = param.replace('m ','')
                memo = memo.replace("\"", '')
                memo = memo.strip()
        self.transaction.Process(date, debit, credit, amount, memo)

    # CONFIGURATION
    def config_create_default(self):
        """Create a default config file."""
        default_config_data = textwrap.dedent("""\
            [Email]
            address=
            password=
            mailbox=
            
            [Paths]
            default=default
            logs=logs
            transactions=transactions
            miscellaneous=miscellaneous""")
        file = open(self.file_config, 'a')
        file.write(default_config_data)
        file.close()

    def config_is_valid(self):
        """Check if the config is valid."""
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.file_config))
        email_account = config.get('Email', 'address')
        if not email_account:
            self.log.info('Config file is not valid. Please enter your information.')
            return False
        else:
            return True

    def config_load(self):
        """Load custom config file settings."""
        config = ConfigParser.ConfigParser()
        config.readfp(open('config.cfg'))
        self.address = config.get('Email','address')
        self.password = config.get('Email','password')
        self.mailbox = config.get('Email', 'mailbox')
        workingdir = os.getcwd() + os.sep
        self.path_default = workingdir + config.get('Paths', 'default')
        # TODO: make path_logs hardcoded
        self.path_logs = workingdir + config.get('Paths', 'logs')
        self.path_transactions = workingdir + config.get('Paths', 'transactions')
        self.path_miscellaneous = workingdir + config.get('Paths', 'miscellaneous')

    def config_setup(self):
        """Setup configuration settings and return if successful."""
        if not os.path.isfile(self.file_config):
            self.config_create_default()
            self.log.info('Created default config file. Please enter your information.')
            return False
        elif self.config_is_valid():
            self.config_load()
            return True
        else:
            return False

    # Initialization
    def main(self):
        """Setup and process email inbox."""
        # TODO: move check for folders up here
        self.log = logger.Logger('Powl')
        config_successful = self.config_setup()
        if config_successful:
            self.check_for_existing_folders()
            self.initialize_modules()
            self.process_inbox()

    def check_for_existing_folders(self):
        """Check if folders exist and if not create them."""
        if not os.path.exists(self.path_logs):
            os.makedirs(self.path_logs)
        if not os.path.exists(self.path_transactions):
            os.makedirs(self.path_transactions)
        if not os.path.exists(self.path_miscellaneous):
            os.makedirs(self.path_miscellaneous)

    def initialize_modules(self):
        """Intialize modules used for doing various actions."""
        self.transaction = TransactionProcessor.\
                           TransactionProcessor(self.path_default,
                                                self.path_transactions,
                                                self.path_logs)
    
if __name__ == '__main__':
    Powl().main()
