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
import powl.logger as logger
from powl.config import Config
from powl.processors.transaction import Transaction

class Main:
    """Class for processing emails to do a corresponding action."""

    # Email Processing
    def process_inbox(self):
        """Parse through an inbox of emails."""
        self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
        self.imap.login(self.config.address, self.config.password)
        self.imap.select(self.config.mailbox)
        search_response, email_ids = self.imap.search(None, "(Unseen)")
        logger.info("PROCESSING INBOX")
        for email_id in email_ids[0].split():
            fetch_response, data = self.imap.fetch(email_id, "(RFC822)")
            mail = email.message_from_string(data[0][1])
            date = email.utils.parsedate(mail['Date'])
            for part in mail.walk():
                if part.get_content_type() == 'text/html':
                    body = part.get_payload()
                    message = self.strip_message_markup(body)
                    logger.debug('EMAIL   %s', message.strip())
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
        filename = os.path.join(self.config.output_dir, 'miscellaneous.txt')
        file = open(filename, 'a')
        file.write(data)
        file.close()
        logger.info('MISC\t%s', data)

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
        self.transaction.process(date, debit, credit, amount, memo)

    # Initialization
    def main(self):
        """Setup and process email inbox."""
        # TODO: move check for folders up here
        self.config = Config()
        self.config.read_config_file()
        log_dir = os.path.join(self.config.output_dir, 'logs')
        logger.initialize(logger.FORMAT_TYPE_DAILY, log_dir)
        self.transaction = Transaction(self.config.qif_filenames,
                                       self.config.qif_types,
                                       self.config.qif_assets,
                                       self.config.qif_liabilities,
                                       self.config.qif_revenues,
                                       self.config.qif_expenses,
                                       self.config.output_dir)
        self.process_inbox()
    

main = Main().main
if __name__ == '__main__':
    main(*sys.argv[1:])