# coding=utf-8
from itertools import chain, imap
import sys
from optparse import OptionParser
import logging
import glob
from fb2tools.book import Book
from lxml.etree import DocumentInvalid
import os
from fb2tools import fb2tag, ArgumentsException, NotAFBZException
from fb2tools.bookcreator import BookCreator, BookStat
from fb2tools.section import Section

logger = logging.getLogger('fb2merge')
frmttr = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')
shdlr = logging.StreamHandler(sys.stderr)
shdlr.setFormatter(frmttr)
logger.addHandler(shdlr)

parser = OptionParser()
parser.add_option('-z', '--zip', dest='zip', action='store_true', default=False)
parser.add_option('-o', '--output', dest='output', action='store')
parser.add_option('-v', '--verbose', dest='debug', action='store_true', default=False)
parser.add_option('-t', '--title', dest='title', action='store')

def main(sys_argv):
    options, args = parser.parse_args(sys_argv[1:])
    logger.setLevel(logging.DEBUG if options.debug else logging.INFO)

    if not options.output:
        raise ArgumentsException('No output specified')
    if not options.title:
        raise ArgumentsException('No book title')

    books_combined = BookCreator(options.title.decode('utf-8'))
    bookstats = BookStat()

    for bookID, file in enumerate(chain(*imap(glob.iglob, args))):
        if not os.path.isfile(file):
            logger.info('Skipping %s: not a file' % file)
            continue

        try:
            book = Book.fromFile(file, True)
        except NotAFBZException:
            logger.warning('Not a valid fbz file: ' + file)
            continue

        bodies = book.getBodies()

        if len(bodies) > 2 or len(bodies) == 0:
            logger.error("Book %s has %d bodies" % (file, len(bodies)))
            continue

        if len(bodies) == 2 and bodies[1].attrib.get('name') != 'notes':
            logger.error("Book %s second body bodies is not [notes]" % file)
            continue

        ## #############################

        bookinfo = bookstats.process(book, bookID)

        ##################

        sp = Section(bodies[0])
        new_section = sp.rebuild_section(
            annotation=book.getAnnotation(),
            cover=book.getCover(),
            epigraphs=book.getEpigraphs(),
            title=book.getTitle(),
        )

        booknotes = []
        if len(bodies) > 1:
            for _pos, noteSection in enumerate(bodies[1]):
                if not noteSection.tag == fb2tag('section'):
                    if _pos or not noteSection.tag == fb2tag('title') :
                        logger.warn("Wrong note: %s in %s" % (noteSection.tag, file))
                    continue

                booknotes.append(noteSection)

        books_combined.insertBook(bookinfo.key, new_section, booknotes)

        for binary in book.getBinaries():
            bID = binary.attrib['id']
            if not bookinfo.referes(bID):
                logger.info('Skipping binary %s' % bID)
                continue

            books_combined.addBinary(binary)

    try:
        book_output = books_combined.finish(bookstats)
        book_output.saveAs(options.output, options.zip)
    except DocumentInvalid, e:
        logger.critical('Not a valid book: %s' % e)

if __name__ == '__main__':
    try:
        main(sys.argv)
    except ArgumentsException, e:
        logger.critical(e)
        sys.exit(1)
