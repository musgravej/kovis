# import pdfrw
import PyPDF2
import os
import re
import datetime
import time
import sys

class Globals:
    def __init__(self):
        # always 202
        self.appid = '202'
        self.year = '2018'
        # mailing date
        self.scan_date = ''


def get_wellmark_id(pdf_file_path):

    pdf_file_obj = open(pdf_file_path, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)

    all_pages = [i for i in range(0, pdf_reader.numPages)]
    name_pages = ([i for i in range(0, pdf_reader.numPages) if ((i + 1) % 4) == 0])

    batch = PyPDF2.PdfFileWriter()
    wid_re = re.compile("\d{3}(AD)\d{4}")
    seq = 1
    for n, i in enumerate(all_pages, 1):
        page_obj = pdf_reader.getPage(i)
        batch.addPage(pdf_reader.getPage(i))
        if i in name_pages:
            text = page_obj.extractText()
            srch = wid_re.search(text)
            srch_cnt = wid_re.findall(text)

            if srch == None:
                print("Skipping: {0} Record: {1}\n{2}\n\n".format(os.path.basename(pdf_file_path), i, text))
            if len(srch_cnt) > 1:
                print(("WARNING!!! Mulitple Matches!!!: "
                       "{0} Record: {1}\n{2}\n\n".format(os.path.basename(pdf_file_path), i, text)))

        # if seq >= 5: break

    pdf_file_obj.close()


def process_pdf(pdf_file_path, g, show_page_lists=False):
    
    print("Processing: {0}".format(os.path.basename(pdf_file_path)))

    # compile regular expressions for searches
    # state_re = re.compile("[a-z, A-Z][a-z, A-Z](?=_Bucket)")
    # bucket_re = re.compile("([0-9]|[0-9][a-z, A-z])(?=_Print)")
    wid_re = re.compile("\d{3}(AD)\d{4}|(W)\d{8}")
    date_string = datetime.datetime.strftime(datetime.datetime.today(),"%m%d%Y%H%M%S")
    # 

    save_dir_name = ('jttocust100001_{timestamp}'.format(timestamp=date_string))

    # Add primary folder
    save_dir_name = os.path.join(save_dir_name, '0')

    # make a new directory to save results in
    if not os.path.exists(save_dir_name) and not show_page_lists:
        os.makedirs(save_dir_name)

    # open the pdf
    pdfFileObj = open(pdf_file_path, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    # make lists of all pages, pages to search WID on, last page of each record
    all_pages = set(i for i in range(0, pdfReader.numPages))
    wid_search_pages = set(i for i in range(0, pdfReader.numPages) if (i % 2) == 0)
    doc_last_pages = set(i for i in range(0, pdfReader.numPages) if (i % 2) == 1)

    # Yes, above could be done more efficiently (because each record is 2 pages), 
    #   but I decided to go with an explicit list as a framework for projects
    #   with more than two pages per record.

    # a little condition for debugging
    if show_page_lists:
        print("** Debug page lists, full processing not done **")
        print("all pages: ", all_pages)
        print("name pages: ", wid_search_pages)
        print("last pages: ", doc_last_pages)
        pdfFileObj.close()
        exit()

    # initialize a couple of variables
    batch = PyPDF2.PdfFileWriter()
    extracted_wid = None
    seq = 0
    for n, i in enumerate(all_pages, 1):
        # where n is the iteratator count, i is the source pdf page number
        pageObj = pdfReader.getPage(i)
        batch.addPage(pdfReader.getPage(i))

        # Create secondary folder
        secondary_dir = int(seq / 100000)
        secondary_dir = os.path.join(save_dir_name, str.zfill(str(secondary_dir), 2))
        if not os.path.exists(secondary_dir):
            os.mkdir(secondary_dir)
        #

        if i in wid_search_pages:
            # search for text, save to variable
            text = pageObj.extractText()
            srch = wid_re.search(text)
            srch_cnt = wid_re.findall(text)

            if len(srch_cnt) > 2:
                print(("WARNING!!! Too Many Matches!!!: "
                       "{0} Record: {1}\n{2}\n\n".format(os.path.basename(pdf_file_path), i, text)))

            if srch is not None:
                extracted_wid = srch[0]
            else:
                print("Skipping: {0} Record: {1}\n{2}\n\n".format(os.path.basename(pdf_file_path), i, text))

        if (i in doc_last_pages) and (i != pdfReader.numPages):
            # write dat file, write out to pdf
            with open(os.path.join(secondary_dir, "{0:0>5}001.pdf".format(seq)), 'wb') as output:
                batch.write(output)
            with open(os.path.join(secondary_dir, "{0:0>5}IDX.dat".format(seq)), 'w') as datfile:
                datfile.write("{appid};1;;;;;;;;;;;{wid};0001;N;{year};{scan}\n".format(wid=extracted_wid,
                                                                                        appid=g.appid,
                                                                                        scan=g.scan_date,
                                                                                        year=g.year))
            seq += 1
            batch = PyPDF2.PdfFileWriter()

    pdfFileObj.close()


def questions():
    print("Processing HCM Kovis\n\n")
    ans = {'week': False, 'scan_date': False}
    qry = int(input("Enter week number (ex: 2): "))
    if qry not in range(1, 6):
        print("Error, Invalid week range (1, 5)")
        return ans
    else:
        ans['week'] = qry

    qry = str(input("Enter scan date MM/DD/YYYY (ex: 10/05/1975): "))
    datere = re.compile("\d{2}/\d{2}/\d{4}")
    if not datere.search(qry):
        print("Error, Invalid date format (MM/DD/YYYY)")
        return ans
    else:
        ans['scan_date'] = qry

    return ans


def find_pdfs(param):
    process_path = os.path.join(os.curdir, 'Week {}'.format(param['week']))
    print_re = re.compile("(Print)")
    pdf_print_files = [f for f in os.listdir(process_path) if print_re.search(f) and f[-3:].upper() == 'PDF']

    pdf_print_files = map(lambda f: os.path.abspath(os.path.join(process_path, f)), pdf_print_files)

    return pdf_print_files


def main():
    param = questions()

    if param['week'] and param['scan_date']:
        g = Globals()
        g.scan_date = param['scan_date']

        for pdf in find_pdfs(param):
            process_pdf(pdf, g)

        print("Kovis processing complete")
        time.sleep(3)
        sys.exit()

    else:
        print("Exiting program")
        time.sleep(3)
        sys.exit()


if __name__ == '__main__':
    main()
