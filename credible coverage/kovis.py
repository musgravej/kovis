# import pdfrw
import PyPDF2
import os
import re
import datetime


class Globals:
    def __init__(self):
        # always 202
        self.appid = '202'
        self.corr_year = '2018'
        # mailing date
        self.scan_date = '10/01/2018'


def get_wellmark_id(pdf_file_path):

    pdfFileObj = open(pdf_file_path, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    all_pages = [i for i in range(0, pdfReader.numPages)]
    name_pages = ([i for i in range(0, pdfReader.numPages) if ((i + 1) % 4) == 0])

    batch = PyPDF2.PdfFileWriter()
    wid_re = re.compile("\d{3}(AD)\d{4}")
    seq = 1
    for n, i in enumerate(all_pages, 1):
        pageObj = pdfReader.getPage(i)
        batch.addPage(pdfReader.getPage(i))
        if i in name_pages:
            text = pageObj.extractText()
            srch = wid_re.search(text)
            srch_cnt = wid_re.findall(text)

            if srch == None:
                print("Skipping: {0} Record: {1}\n{2}\n\n".format(os.path.basename(pdf_file_path), i, text))
            if len(srch_cnt) > 1:
                print(("WARNING!!! Mulitple Matches!!!: "
                       "{0} Record: {1}\n{2}\n\n".format(os.path.basename(pdf_file_path), i, text)))

        # if seq >= 5: break

    pdfFileObj.close()


def process_pdf(pdf_file_path):
    print("Processing: {0}".format(os.path.basename(pdf_file_path)))

    state_re = re.compile("[a-z, A-Z][a-z, A-Z](?=_Bucket)")
    bucket_re = re.compile("([0-9]|[0-9][a-z, A-z])(?=_Print)")
    wid_re = re.compile("\d{3}(AD)\d{4}")
    date_string = datetime.datetime.strftime(datetime.datetime.today(),"%m%d%Y%H%M%S")

    save_dir_name = ('jttocust100001_{state}{bucket}_{timestamp}'.format(state=state_re.search(pdf_file_path)[0],
                                                                         bucket=bucket_re.search(pdf_file_path)[0],
                                                                         timestamp=date_string))

    # Add primary folder
    save_dir_name = os.path.join(save_dir_name, '0')

    if not os.path.exists(save_dir_name):
        os.makedirs(save_dir_name)

    pdfFileObj = open(pdf_file_path, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    all_pages = [i for i in range(0, pdfReader.numPages)]
    name_pages = ([i for i in range(0, pdfReader.numPages) if ((i + 1) % 4) == 0])

    batch = PyPDF2.PdfFileWriter()
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


        if i in name_pages:
            with open(os.path.join(secondary_dir, "{0:0>5}001.pdf".format(seq)), 'wb') as output:
                batch.write(output)
            with open(os.path.join(secondary_dir, "{0:0>5}IDX.dat".format(seq)), 'w') as datfile:
                text = pageObj.extractText()
                srch = wid_re.search(text)
                srch_cnt = wid_re.findall(text)

                if len(srch_cnt) > 1:
                    print(("WARNING!!! Mulitple Matches!!!: "
                           "{0} Record: {1}\n{2}\n\n".format(os.path.basename(pdf_file_path), i, text)))

                if srch is not None:
                    datfile.write("{appid};1;;;;;;;;;;;{wid};0001;N;2011;{scan}\n".format(wid=srch[0],
                                                                                          appid=Globals().appid,
                                                                                          scan=Globals().scan_date))
                else:
                    print("Skipping: {0} Record: {1}\n{2}\n\n".format(os.path.basename(pdf_file_path), i, text))
            seq += 1
            if i != pdfReader.numPages:
                batch = PyPDF2.PdfFileWriter()

        # if seq >= 5: break
    pdfFileObj.close()


if __name__ == '__main__':

    process_path = os.path.join(os.curdir, 'pdf', 'Proof and Print Files','IA')
    # process_path = os.path.join(os.curdir, 'pdf', 'Proof and Print Files','SD')

    print_re = re.compile("(Print)")
    pdf_print_files = [f for f in os.listdir(process_path) if print_re.search(f)]

    pdf_print_files = map(lambda f: os.path.abspath(os.path.join(process_path, f)), pdf_print_files)

    for n, pdf in enumerate(pdf_print_files, 1):
        process_pdf(pdf)
        # if n >= 1: break
        # get_wellmark_id(pdf)