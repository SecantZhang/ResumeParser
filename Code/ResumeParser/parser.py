import csv
import re
import json

from datetime import datetime
import pdfminer
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTTextBoxHorizontal, LTTextBoxVertical
from pdfminer.converter import PDFPageAggregator
from bson import ObjectId
import gridfs
import unicodedata
import datefinder
from pdfminer.converter import TextConverter
from cStringIO import StringIO
from education_detail import Education
from user_detail import User
import sys
from pyzipcode import ZipCodeDatabase
import nltk
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import itertools

reload(sys)
sys.setdefaultencoding('utf-8')


key_file_path = "key.csv"
text_dict = {}
text_prop_dict = {}
user_id = 1
visited = []
pdf_to_text_list = []
text_list_p1 = []
string_p1 = ""
text_list_p2 = []
string_p2 = ""
text_list_p3 = []
string_p3 = ""
output_list_p1 = []
output_list_p2 = []
output_list_p3 = []
output_json = ""
dir_path = "wordList/"

# def convert_output_list_to_json(list1, list2, list3):
#     output_json = '{ "part1": { "skills": { '
#     for i in range(0,len(list1[1])-1):
#         if i != len(list1[1]):
#             output_json += ('"' + str(list1[1][i]) + '" : 1,' + )
#         else:
#             output_json += ('"' + str(list1[1][i]) + '"')




def checking_sections(list_segment, identi_str):
    global output_list_p1, output_list_p2, output_list_p3
    global string_p1, string_p2, string_p3
    outlist = []
    sum_list = []
    sum_list += [re.split(', |                       |: |\xe2\x80\xa2', i) for i in list_segment]
    merged = filter(None, list(itertools.chain.from_iterable(sum_list)))
    result_list = filter(None, [x.strip(' ') for x in merged])
    # print identi_str, result_list
    # Re-initialize the section list. 
    if any(item in string_p1 for item in result_list):
        temp_list = []
        output_list_p1.append(identi_str)
        bool_list_p1 = [item in string_p1 for item in result_list]
        for i,j in zip(bool_list_p1, result_list):
            if i:
                temp_list.append(j)
        output_list_p1.append(temp_list)

    if any(item in string_p2 for item in result_list):
        temp_list = []
        output_list_p2.append(identi_str)
        bool_list_p2 = [item in string_p2 for item in result_list]
        for i,j in zip(bool_list_p2, result_list):
            if i:
                temp_list.append(j)
        output_list_p2.append(temp_list)

    if any(item in string_p3 for item in result_list):
        temp_list = []
        output_list_p3.append(identi_str)
        bool_list_p3 = [item in string_p3 for item in result_list]
        for i,j in zip(bool_list_p3, result_list):
            if i:
                temp_list.append(j)
        output_list_p3.append(temp_list)
    

    # if identi_str == "SKILL":
    #     print identi_str, result_list
    #     print string_p1
    



def convert_pdf_to_txt(fileObj):
    """
    This function takes the file object and converts the file content to simple text format

    :param fileObj: File object for reading the file
    :return: None
    """

    global pdf_to_text_list, string_p1, string_p2, string_p3

    # Convert pdf document into text document
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(fileObj, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)


    text = str(retstr.getvalue().encode('utf-8'))
    text = re.sub(r'\n\s*\n', '\n', text)
    pdf_to_text_list = text.split("\n")

    # Split the text_list into 3 parts. 
    temp_size = len(pdf_to_text_list)
    for i in range(0, temp_size):
        # Top section
        if i in range(0, int(temp_size/3)):
            text_list_p1.append(pdf_to_text_list[i])
        elif i in range(int(temp_size/3), int(temp_size/3) * 2):
            text_list_p2.append(pdf_to_text_list[i])
        else:
            text_list_p3.append(pdf_to_text_list[i])

    string_p1 = ''.join(text_list_p1)
    string_p2 = ''.join(text_list_p2)
    string_p3 = ''.join(text_list_p3)

    # print "p1---------------", string_p1
    # print "p2---------------", string_p2
    # print "p3---------------", string_p3

def read_pdf_miner(fileObj):
    """
    This function takes the file object, read the file content and store it into a dictionary for processing

    :param fileObj: File object for reading the file
    :return: None
    """
    # Create a PDF parser object associated with the file object.
    parser = PDFParser(fileObj)

    # Create a PDF document object that stores the document structure.
    document = PDFDocument(parser)

    # Check if the document allows text extraction. If not, abort.
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed

    # Create a PDF resource manager object that stores shared resources.
    rsrcmgr = PDFResourceManager()

    # Create a PDF device object.
    device = PDFDevice(rsrcmgr)

    # BEGIN LAYOUT ANALYSIS
    # Set parameters for analysis.
    laparams = LAParams()

    # Create a PDF page aggregator object.
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)

    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # loop over all pages in the document
    for page in PDFPage.create_pages(document):

        # read the page into a layout object
        interpreter.process_page(page)

        layout = device.get_result()

        id = 0
        for lt_obj in layout:

            # save horizontal text box content
            if isinstance(lt_obj, LTTextBoxHorizontal):
                text_dict[id] = lt_obj.get_text()
                text_prop_dict[id] = lt_obj
                id += 1


def extract_user_detail():
    """
    This function extracts user personal data like name, address, phone, email and profile links
    from the resume

    :return: None
    """

    top_text_id = -1
    max_val = -100000000

    """
    Extract Name: Iterate all the layout objects to get the text which is present
    at the top of the page which is the name of the person
    """
    for key, lt_obj in text_prop_dict.iteritems():
        if (lt_obj.bbox[1] > max_val and not lt_obj.get_text().isspace()):
            top_text_id = key
            max_val = lt_obj.bbox[1]


    def get_name(top_text_id):
        """
        Extract name from the text
        """

        email_flag = False
        phone_flag = False
        link_flag = False

        name_object = text_prop_dict.get(top_text_id)
        text = name_object.get_text()
        text = str(unicodedata.normalize('NFKD', text).encode('utf-8')).strip()
        sentences = nltk.sent_tokenize(text)
        sentences = [nltk.word_tokenize(sent) for sent in sentences]
        sentences = [nltk.pos_tag(sent) for sent in sentences]
        full_name = []

        for item in sentences[0]:

            # convert tuple to list
            item_list = list(item)

            # Search consecutive Proper Noun
            if 'NNP' in item_list and (item_list[0].istitle() or str(item_list[0]).isupper()):
                full_name.append(item_list[0])
            else:
                break

        # check email in name object
        index = text.find("@")
        if index > 0:
            email_flag = True

        # check phone number in name object
        cell = re.search("\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}", text)
        if cell:
            phone_flag = True
        name = " ".join(full_name)

        # check hyperlinks in name object
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        if len(urls) > 0:
            link_flag = True

        return name, email_flag, phone_flag, link_flag

    def get_email(text):
        """
        Search email using regex from the given text
        :param text: Text which consist of email address
        :return: None
        """

        text = str(unicodedata.normalize('NFKD', text).encode('utf-8'))
        index = text.find("@")
        if index > 0:
            email = re.search(r'[\w\.-]+@[\w\.-]+', text)
            if email:
                return email.group(0)
        else:
            for k,v in text_dict.iteritems():
                v = str(unicodedata.normalize('NFKD', v).encode('utf-8'))
                text = re.search(r'[\w\.-]+@[\w\.-]+', v)
                if text:
                    return text.group(0)
        return None

    def get_cell(text):

        text = str(unicodedata.normalize('NFKD', text).encode('utf-8'))
        cell = re.search("\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}", text)
        if cell:
            return cell.group(0)
        else:
            for k,v in text_dict.iteritems():
                v = str(unicodedata.normalize('NFKD', v).encode('utf-8'))
                cell = re.search("\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}", v)

                if cell:
                    return cell.group(0)
            return None

    def get_zipcode(text):

        text = str(unicodedata.normalize('NFKD', text).encode('utf-8'))
        zip_code = re.search(r'\b\d{5}(?:[-\s]\d{4})?\b', text)
        # print zip_code
        if zip_code:
            return zip_code.group(0)
        else:
            for k,v in text_dict.iteritems():
                v = str(unicodedata.normalize('NFKD', v).encode('utf-8'))
                zip_code = re.search(r'\b\d{5}(?:[-\s]\d{4})?\b', v)
                if zip_code:
                    return zip_code.group(0)
        return None

    def get_links(text):

        text = str(unicodedata.normalize('NFKD', text).encode('utf-8'))
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)

        if len(urls) > 0:
            return urls
        else:
            result = []
            for k, v in text_dict.iteritems():
                v = str(unicodedata.normalize('NFKD', v).encode('utf-8'))
                urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',v)
                if len(urls) > 0:
                    result.extend(urls)
        return result

    user = User()

    neighbor = find_neighbor(top_text_id)

    full_name, email_flag, phone_flag, link_flag = get_name(top_text_id)
    user.set_full_name(full_name)

    if not email_flag and not neighbor == None:
        user.set_email(get_email(neighbor.get_text()))
    else:
        name_object = text_prop_dict.get(top_text_id)
        text = name_object.get_text()
        user.set_email(get_email(text))

    if not phone_flag and not neighbor == None:
        user.set_phone(get_cell(neighbor.get_text()))
    else:
        name_object = text_prop_dict.get(top_text_id)
        text = name_object.get_text()
        user.set_phone(get_cell(text))

    if not neighbor == None:

        zipcode = get_zipcode(neighbor.get_text())

        if zipcode != None:
            # Use zipcode dictionary to find state and city
            search = ZipCodeDatabase()
            zip_obj = search[zipcode]
            state = zip_obj.state
            city = zip_obj.city
            user.set_addr(None,city, state, "USA", zipcode)
        else:
            user.set_addr(None, None, None, None, None)

    if not link_flag and not neighbor == None:
        user.set_link(get_links(neighbor.get_text()))
    else:
        name_object = text_prop_dict.get(top_text_id)
        text = name_object.get_text()
        user.set_link(get_links(text))

    # user.display()
    # show_object(neighbor)
    return user


def find_neighbor(key):
    """
    This function will find closest text to the given text in the resume layout
    """
    global visited

    min_vdist, min_hdist = 1000000, 1000000
    id = 0
    neighbor = ""
    name_object = text_prop_dict.get(key)
    visited.append(name_object)

    for k, lt_obj in text_prop_dict.iteritems():
        # print "Key: ", k, "     vdist: ", name_object.vdistance(lt_obj), "              hdist: ", name_object.hdistance(
        #     lt_obj), "            voverlap: ", name_object.voverlap(lt_obj), "     hoverlap: ", name_object.hoverlap(
        #     lt_obj)
        # # print name_object.vdistance(lt_obj) <= min_vdist, name_object.hdistance(lt_obj) <= min_hdist
        # print lt_obj.get_text()
        # text = str(unicodedata.normalize('NFKD', lt_obj.get_text()).encode('utf-8'))
        # sentences = nltk.sent_tokenize(text)
        # sentences = [nltk.word_tokenize(sent) for sent in sentences]
        # sentences = [nltk.pos_tag(sent) for sent in sentences]
        # print sentences
        # print "\n\n\n"
        if (name_object.vdistance(lt_obj) + name_object.hdistance(lt_obj) <= (min_hdist + min_vdist)):
            if (not (name_object.vdistance(lt_obj) == 0 and name_object.hdistance(lt_obj) == 0)):
                text = str(unicodedata.normalize('NFKD', lt_obj.get_text()).encode('utf-8'))
                if text.__contains__("@"):
                    min_vdist = name_object.vdistance(lt_obj)
                    min_hdist = name_object.hdistance(lt_obj)
                    neighbor = lt_obj
                    id = k
    if neighbor == "":
        return None

    visited.append(neighbor)
    return neighbor


def create_segments():
    education_segment = []
    work_segment = []
    user_segment = []
    project_segment = []
    skill_segment = []
    other_segment = []

    def get_keywords(file_name):
        reader = read_csv(dir_path + file_name)
        keywords = []
        for row in reader:
            keywords.append(row[0])
        return keywords

    def get_qualification_word_list(dir_path):
        file_name = "qualification_degree_list.csv"
        reader = read_csv(dir_path+file_name)
        qualification_word_dict = {}
        abbr_list = []
        degree_list = []
        for row in reader:
            abbr_list.append(row[0])
            degree_list.append(row[1])
            qualification_word_dict[row[0]] = row[1]
        return qualification_word_dict, abbr_list, degree_list

    def get_major_word_list(dir_path):
        file_name = "educational_major.csv"
        reader = read_csv(dir_path + file_name)
        major_list = []
        for row in reader:
            major_list.append(row[0])
        return major_list

    def get_university_word_list(dir_path):
        file_name = "university.csv"
        reader = read_csv(dir_path + file_name)
        university_word_dict = {}
        for row in reader:
            value = [row[2], row[3], row[4], row[5]]
            university_word_dict[row[1]] = value
        return university_word_dict

    def search_keyword(text, keyword_list):
        for word in keyword_list:
            word = str(word)
            if word.title() in text or word.upper() in text or word.capitalize() in text:
                return True
        return False

    def load_user_segment():

        def validate_text(text):

            if text.find("GPA") > 0:
                # print "GPA found"
                education_segment.append(text)
                return False

            return True

        # Extract User Segment
        for i, text in enumerate(pdf_to_text_list):
            if not search_keyword(text, education_keywords) and not search_keyword(text,education_degree_category) and not search_keyword(
                text, project_keywords) and not search_keyword(text, skill_keywords) and not search_keyword(
                text, other_keywords) and not search_keyword(text, work_experience_keywords):

                if validate_text(text):
                    user_segment.append(text)
            else:
                break

    def load_work_segment():

        def validate_text(text):

            # check email in name object
            if text.find("@") > 0 or text.find("github.com") >= 0 or text.find("linkedin.com") >= 0:
                user_segment.append(text)
                # print "Email found"
                return False

            # check phone number in name object
            cell = re.search("\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}",
                             text)
            if cell:
                # print "Cell found"
                user_segment.append(text)
                return False

            # check hyperlinks in name object
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
            if len(urls) > 0:
                # print "link found"
                user_segment.append(text)
                return False

            if text.find("GPA") > 0:
                # print "GPA found"
                education_segment.append(text)
                return False

            return True

        # Extract Work Segment
        for i, text in enumerate(pdf_to_text_list):
            flag = False
            if search_keyword(text, work_experience_keywords):
                work_segment.append(text)
                i += 1
                flag = True
                while True:
                    text = pdf_to_text_list[i]
                    if not search_keyword(text, education_keywords) and not search_keyword(text,
                                                                                          education_degree_category) and not search_keyword(
                            text, project_keywords) and not search_keyword(text, skill_keywords) and not search_keyword(
                            text, other_keywords):

                        if validate_text(text):
                            work_segment.append(text)
                    else:
                        break
                    i += 1

            if flag:
                break

    def load_education_segment():

        def validate_text(text):

            # check email in name object
            if text.find("@") > 0 or text.find("github.com") >= 0 or text.find("linkedin.com") >= 0:
                user_segment.append(text)
                # print "Email found"
                return False

            # check phone number in name object
            cell = re.search("\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}",
                             text)
            if cell:
                # print "Cell found"
                user_segment.append(text)
                return False

            # check hyperlinks in name object
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
            if len(urls) > 0:
                # print "link found"
                user_segment.append(text)
                return False

            return True

        # Extract Education Segment
        for i, text in enumerate(pdf_to_text_list):
            flag = False
            if search_keyword(text, education_keywords):
                education_segment.append(text)
                i += 1
                flag = True
                while True and i < len(pdf_to_text_list):

                    text = pdf_to_text_list[i]
                    if not search_keyword(text, work_experience_keywords) and not search_keyword(
                        text, project_keywords) and not search_keyword(text, skill_keywords) and not search_keyword(
                        text, other_keywords):
                        if validate_text(text):
                            education_segment.append(text)
                    else:
                        break
                    i += 1
            if flag:
                break

    def load_skill_segment():

        # Extract Skill Segment
        for i, text in enumerate(pdf_to_text_list):
            flag = False
            if search_keyword(text, skill_keywords):
                skill_segment.append(text)
                i += 1
                flag = True
                while True and i < len(pdf_to_text_list):
                    text = pdf_to_text_list[i]
                    if not search_keyword(text, education_keywords) and not search_keyword(text,
                                                                                          education_degree_category) and not search_keyword(
                            text, project_keywords) and not search_keyword(text, work_experience_keywords) and not search_keyword(
                            text, other_keywords):
                        skill_segment.append(text)
                    else:
                        break
                    i += 1

            if flag:
                break

    def load_project_segment():
        # Extract Project Segment
        for i, text in enumerate(pdf_to_text_list):
            flag = False
            if search_keyword(text, project_keywords):
                project_segment.append(text)
                i += 1
                flag = True
                while True and i < len(pdf_to_text_list):
                    text = pdf_to_text_list[i]
                    if not search_keyword(text, education_keywords) and not search_keyword(text, education_degree_category) and not search_keyword(
                        text, skill_keywords) and not search_keyword(text, work_experience_keywords) and not search_keyword(
                        text, other_keywords):
                        project_segment.append(text)
                    else:
                        break
                    i += 1

            if flag:
                break

    def load_other_segment():
        # Extract Other Segment
        for i, text in enumerate(pdf_to_text_list):
            flag = False
            if search_keyword(text, other_keywords):
                other_segment.append(text)
                i += 1
                flag = True
                while True and i < len(pdf_to_text_list):
                    text = pdf_to_text_list[i]
                    if not search_keyword(text, education_keywords) and not search_keyword(text,
                                                                                          education_degree_category) and not search_keyword(
                            text, skill_keywords) and not search_keyword(text,
                                                                         work_experience_keywords) and not search_keyword(
                        text, project_keywords):
                        other_segment.append(text)
                    else:
                        break
                    i += 1

            if flag:
                break

    def show(l):
        for row in l:
            print row

    def parse_user_segment():

        user = extract_user_detail()

        for text in user_segment:

            if str(text).isupper():
                if user.get_full_name() == "":
                    user.set_full_name(text)

            if text.find("@") > 0:
                if user.get_email() == "":
                    user.set_email(text)

            if text.find("github.com") >= 0 or text.find("linkedin.com") >= 0:
                if text not in user.get_link():
                    temp = user.get_link()
                    if temp == None:
                       temp = [text]
                    else:
                       temp.append(text)
                    user.set_link(temp)

            # check phone number in name object
            cell = re.search(
                "\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}",
                text)
            if cell and user.get_phone() == "":
                user.set_phone(text)
        return user

    def parse_education_segment(user):

        def find_date_degree_major_gpa(text, date_flag, degree_flag, major_flag):
            max_len = 0
            # Find GPA
            index = text.find("GPA")
            if index >= 0:
                edu_obj.gpa = (text[index + 4:]).strip()

            # Find Date
            if not date_flag:
                matches = list(datefinder.find_dates(text))
                edu_date = ""
                if not matches == []:
                    currentYear = datetime.now().year
                    for temp_date in matches:
                        if not temp_date.year > currentYear + 4:
                            edu_date += str(temp_date.month) + "/" + str(temp_date.year) + " - "
                    edu_obj.year = edu_date[:(len(edu_date) - 2)]
                    date_flag = True

            # Find Degree and Major
            if not degree_flag:
                for abbr, val in qualification_word_dict.iteritems():
                    score1 = fuzz.ratio(str(abbr).lower(), text.lower())
                    score2 = fuzz.ratio(str(val).lower(), text.lower())
                    if score1 > 90 or score2 > 90 and max_len < len(val):
                        max_len = len(val)
                        degree = val

                    if not major_flag and str(abbr).lower() in text.lower():
                        edu_obj.major = val
                        major_flag = True

                for word in major_word_list:
                    score3 = fuzz.partial_ratio(str(word).lower(), text.lower())
                    if score3 > 90 and max_len < len(word):
                        max_len = len(word)
                        degree = word
                        edu_obj.degree = degree
                        date_flag = True


            return  date_flag, degree_flag, major_flag

        degree_category = ['associate', 'bachelor', 'master', 'doctoral']
        text = str(education_segment[0])

        # remove Education segment keyword
        for word in education_keywords:
            word = str(word)
            if word.title() in text or word.upper() in text or word.capitalize() in text:
                text = text.replace(word.title(), '')
                text = text.replace(word.upper(), '')
                text = text.replace(word.capitalize(), '')
                education_segment[0] = text
                break

        # Find indexes of all university
        max_score, longest_length = 0, 0
        closest_university_1, closest_university_2 = "", ""
        university_flag = False
        degree_flag = False
        date_flag = False
        major_flag = False
        edu_obj = Education()
        user.education = edu_obj
        for i in range(0,len(education_segment)):
            text = education_segment[i]

            if not university_flag:
                for university, addr_list in university_word_dict.iteritems():

                    if university in text and longest_length < len(university):
                        longest_length = len(university)
                        closest_university_1 = university
                        university_flag = True

                    score = fuzz.ratio(str(university).lower(), text.lower())
                    # print university, score
                    if score > 90 and max_score < score and not text == " ":
                        # print score, university, [text]
                        max_score = score
                        closest_university_2 = university
                        university_flag = True

                if university_flag:
                    if len(closest_university_1) > len(closest_university_2):
                        closest_university = closest_university_1
                    else:
                        closest_university = closest_university_2
                    edu_obj.university = closest_university
                    addr_list = university_word_dict.get(closest_university)
                    edu_obj.set_addr(addr_list[0], addr_list[1], addr_list[2], "USA", addr_list[3])

                    j = i
                    while(True):
                        max_len = 0
                        degree = ""

                        # Find GPA
                        index = text.find("GPA")

                        if index >= 0:
                            edu_obj.gpa = (text[index+4:]).strip()

                        # Find Date
                        if not date_flag:
                            matches = list(datefinder.find_dates(text))
                            edu_date = ""
                            if not matches == []:
                                currentYear = datetime.now().year
                                for temp_date in matches:
                                    if not temp_date.year > currentYear + 4:
                                        edu_date += str(temp_date.month) + "/" + str(temp_date.year) + " - "
                                edu_obj.year = edu_date[:(len(edu_date) - 2)]
                                date_flag = True

                        # Find Degree and Major
                        # major_flag = False
                        if not degree_flag:
                            for abbr, val in qualification_word_dict.iteritems():
                                score1 = fuzz.ratio(str(abbr).lower(), text.lower())
                                score2 = fuzz.ratio(str(val).lower(), text.lower())
                                if score1 > 90 or score2 > 90 and max_len < len(val):
                                    max_len = len(val)
                                    degree = val

                                if not major_flag and str(abbr).lower() in text.lower():
                                    edu_obj.major = val
                                    major_flag = True

                            for word in major_word_list:
                                score3 = fuzz.partial_ratio(str(word).lower(), text.lower())
                                if score3 > 90 and max_len < len(word):
                                    max_len = len(word)
                                    degree = word

                        if not max_len == 0 and not degree_flag:
                            edu_obj.degree = degree
                            degree_flag = True

                        if not edu_obj.gpa == "" and degree_flag or i >= len(education_segment):
                            break

                        i += 1

                        if not i >= len(education_segment):
                            text = education_segment[i]
                        else:

                            # Iterate from 0 until the index at which university was found
                            k = 0
                            while k < j:
                                text = education_segment[k]
                                # Find GPA
                                if edu_obj.gpa == "":
                                    index = text.find("GPA")
                                    # print [text], index
                                    if index >= 0:
                                        edu_obj.gpa = (text[index + 4:]).strip()

                                # Find Date
                                if edu_obj.year == "":
                                    matches = list(datefinder.find_dates(text))
                                    edu_date = ""
                                    if not matches == []:
                                        currentYear = datetime.now().year
                                        for temp_date in matches:
                                            if not temp_date.year > currentYear + 4:
                                                edu_date += str(temp_date.month) + "/" + str(temp_date.year) + " - "
                                        edu_obj.year = edu_date[:(len(edu_date) - 2)]
                                        date_flag = True

                                # Find Degree
                                if edu_obj.degree == "":
                                    for abbr, val in qualification_word_dict.iteritems():
                                        score1 = fuzz.ratio(str(abbr).lower(), text.lower())
                                        score2 = fuzz.ratio(str(val).lower(), text.lower())
                                        if score1 > 90 or score2 > 90 and max_len < len(val):
                                            max_len = len(val)
                                            degree = val

                                    if not major_flag and str(abbr).lower() in text.lower():
                                        edu_obj.major = val
                                        major_flag = True

                                    for word in major_word_list:
                                        score3 = fuzz.partial_ratio(str(word).lower(), text.lower())
                                        if score3 > 90 and max_len < len(word):
                                            max_len = len(word)
                                            degree = word
                                k+=1

                            break

                else:
                    # Search before university name in the education segment
                    date_flag, degree_flag, major_flag = find_date_degree_major_gpa(text, date_flag, degree_flag, major_flag)

        if edu_obj.university == "":
            # print "Call Old method"
            extract_education_detail(edu_obj)

    def parse_work_segment():

        text = str(work_segment[0])
        # remove work segment keyword
        for word in work_experience_keywords:
            word = str(word)
            if word.title() in text or word.upper() in text or word.capitalize() in text:
                text = text.replace(word.title(),'')
                text = text.replace(word.upper(), '')
                text = text.replace(word.capitalize(), '')
                work_segment[0] = text
                break

        month = ['january','february','march','april','may','june','july','aug','september','october','november',
                 'december','jan','feb','mar','apr','jun','jul','aug','sep','oct','nov','dec']

        work_dict = {}

        # for i,text in enumerate(work_segment):
        j = 0
        for i in range(0,len(work_segment)):
            text = work_segment[i]
            if search_keyword(text, month):
                work_dict[text] = []
                i+=1
                while(True):
                    if i < len(work_segment) and not search_keyword(work_segment[i], month):
                        temp = work_dict.get(text)
                        temp.append(work_segment[i])
                        work_dict[text] = temp
                        i += 1
                    else:
                        break
        return work_dict

    # Load all keyword word list for segments
    education_keywords = get_keywords("education_segment.csv")
    work_experience_keywords = get_keywords("work_experience_segment.csv")
    education_degree_category = get_keywords("degree_category.csv")
    project_keywords = get_keywords("project_segment.csv")
    skill_keywords = get_keywords("skill_segment.csv")
    other_keywords = get_keywords("accomplishment_segment.csv")

    # Load degree, major, university wordlist for education segment
    qualification_word_dict, abbr_list, degree_list = get_qualification_word_list(dir_path)
    university_word_dict = get_university_word_list(dir_path)
    major_word_list = get_major_word_list(dir_path)

    # Load all segments
    load_user_segment()
    load_work_segment()
    load_education_segment()
    load_skill_segment()
    load_project_segment()
    load_other_segment()

    # print "***************************************************************************************************"
    # print "User segment: ", show(user_segment)
    # print "***************************************************************************************************"
    # print "Work segment: ", show(work_segment)
    # print "***************************************************************************************************"
    # print "Education segment: ",show(education_segment)
    # print "***************************************************************************************************"
    # print "Skill segment: ", show(skill_segment)
    # print "***************************************************************************************************"
    # print "Project segment: ", show(project_segment)
    # print "***************************************************************************************************"
    # print "Other segment: ", show(other_segment)
    # print "***************************************************************************************************"
    # print "Complete Strings: ", show(pdf_to_text_list)
    # print "\n\n"
    # print "SKILLS---", skill_segment


    user = parse_user_segment()
    parse_education_segment(user)
    user.education.display()

    # Checking Skills in different sections. 
    # Prepare the related list. 
    checking_sections(skill_segment, "SKILL")
    # checking_sections(education_segment, "EDUCATION")
    # checking_sections(project_segment, "PROJECT")
    # checking_sections(user_segment, "USER")

    print "PART1", output_list_p1, "\n------------------------------------------------\n"
    print "PART2", output_list_p2, "\n------------------------------------------------\n"
    print "PART3", output_list_p3, "\n------------------------------------------------\n"
    # print string_p1, "\n------------------------------------------------\n"
    # print string_p2, "\n------------------------------------------------\n"
    # print string_p3, "\n------------------------------------------------\n"
    # work_dict = parse_work_segment()
    # for k,v in work_dict.items():
    #     print k.strip()
    #     for row in v:
    #         print row.strip()
    #     print ""
    #
    # display_list()


def extract_work_exp_detail(user):

    def get_company_list():
        file_name = "companies.csv"
        reader = read_csv(dir_path + file_name)
        companies_word_list = []
        for row in reader:
            companies_word_list.append(row[0])
        return companies_word_list

    def get_work_experience_keywords():
        file_name = "work_experience_segment.csv"
        reader = read_csv(dir_path + file_name)
        work_experience_keywords = []
        for row in reader:
            work_experience_keywords.append(row[0])
        return work_experience_keywords

    def check_blank_lines(text):
        numbers = sum(c.isdigit() for c in text)
        words = sum(c.isalpha() for c in text)
        spaces = sum(c.isspace() for c in text)
        others = len(text) - numbers - words - spaces
        if spaces == len(text):
            return True
        else:
            return False

    def closest_neighbor(work_exp_obj):
        min_vdist, min_hdist = 1000000, 1000000
        neighbor = ""

        for k, lt_obj in text_prop_dict.iteritems():

            text = str(unicodedata.normalize('NFKD', lt_obj.get_text()).encode('utf-8'))

            if (work_exp_obj.vdistance(lt_obj) + work_exp_obj.hdistance(lt_obj) <= (min_hdist + min_vdist) and not check_blank_lines(text)):
                if (not (work_exp_obj.vdistance(lt_obj) == 0 and work_exp_obj.hdistance(lt_obj) == 0)):
                    text = str(unicodedata.normalize('NFKD', lt_obj.get_text()).encode('utf-8'))
                    min_vdist = work_exp_obj.vdistance(lt_obj)
                    min_hdist = work_exp_obj.hdistance(lt_obj)
                    neighbor = lt_obj

        return neighbor

    def find_work_experience_segment():

        flag = False
        for k, lt_obj in text_prop_dict.iteritems():
            text = str(unicodedata.normalize('NFKD', lt_obj.get_text()).encode('utf-8'))

            # print [text]
            for word in work_experience_keywords:
                word = str(word)
                if word.title() in text or word.upper() in text or word.capitalize() in text:
                    flag = True

                    neighbor = closest_neighbor(lt_obj)
                    neighbor_text = str(unicodedata.normalize('NFKD', neighbor.get_text()).encode('utf-8'))
                    break

            if flag:
                break
        # display()

    companies_word_list = get_company_list()
    work_experience_keywords = get_work_experience_keywords()
    find_work_experience_segment()


def extract_education_detail(edu_obj):

    def get_education_word_list(dir_path):
        file_name = "education_segment.csv"
        reader = read_csv(dir_path+file_name)
        education_word_list = []
        for row in reader:
            education_word_list.append(row[0])
        return education_word_list

    def get_qualification_word_list(dir_path):
        file_name = "qualification_degree_list.csv"
        reader = read_csv(dir_path+file_name)
        qualification_word_dict = {}
        abbr_list = []
        degree_list = []
        for row in reader:
            # print row
            abbr_list.append(row[0])
            degree_list.append(row[1])
            qualification_word_dict[row[0]] = row[1]
        return qualification_word_dict, abbr_list, degree_list

    def get_major_word_list(dir_path):
        file_name = "educational_major.csv"
        reader = read_csv(dir_path + file_name)
        major_list = []
        for row in reader:
            major_list.append(row[0])
        return major_list

    def get_university_word_list(dir_path):
        file_name = "university.csv"
        reader = read_csv(dir_path + file_name)
        university_word_dict = {}
        for row in reader:
            value = [row[2], row[3], row[4], row[5]]
            university_word_dict[row[1]] = value
        return  university_word_dict

    def search_major(text, degree, edu_obj):

        degree_flag = False
        max = -1
        # Search for major
        for major in major_word_list:
            if major.lower() in (text.lower()) and len(major) > max:
                edu_obj.major = str(major).title()
                edu_obj.degree = degree.title()
                max = len(str(major))
                degree_flag = True

        return degree_flag

    def search_date(text, edu_obj):

        # Search for Date
        matches = list(datefinder.find_dates(text))
        edu_date = ""
        if not matches == []:
            currentYear = datetime.now().year
            for temp_date in matches:
                if not temp_date.year > currentYear + 4:
                    edu_date += str(temp_date.month) + "/" + str(temp_date.year) + " - "
            edu_obj.year = edu_date[:(len(edu_date) - 2)]
            date_flag = True

    def closest_neighbor(name_object,edu_obj, degree_list):
        global visited

        visited.append(name_object)
        date_flag, gpa_flag = False, False
        for k, lt_obj in text_prop_dict.iteritems():

            text = str(unicodedata.normalize('NFKD', lt_obj.get_text()).encode('utf-8'))
            if lt_obj not in visited:

                max_score = 0
                closest_university = ""
                university_flag = False
                for university, addr_list in university_word_dict.iteritems():

                    score = fuzz.partial_ratio(str(university).lower(), text.lower())

                    if score > 90 and max_score < score:
                        max_score = score
                        closest_university = university
                        university_flag = True

                if university_flag:
                    degree_flag = False

                    # Search for degree
                    for degree in degree_list:
                        if degree.lower() in text.lower():
                            edu_obj.university = closest_university
                            addr_list = university_word_dict.get(closest_university)
                            edu_obj.set_addr(addr_list[0], addr_list[1], addr_list[2], "USA", addr_list[3])
                            degree_flag = search_major(text, degree, edu_obj)

                    # Search for degree if not found earlier
                    if not degree_flag:
                        degree_flag = search_major(text, degree, edu_obj)
                        edu_obj.university = closest_university
                        addr_list = university_word_dict.get(closest_university)
                        edu_obj.set_addr(addr_list[0], addr_list[1], addr_list[2], "USA", addr_list[3])
                        for key, val in qualification_word_dict.iteritems():
                            if key in text:
                                edu_obj.degree = val
                                degree_flag = True
                            if val in text and edu_obj.major == "":
                                edu_obj.major = val
                    # search_date(text, edu_obj)

                    # Find GPA
                    if not gpa_flag:
                        index = text.find("GPA")
                        if index >= 0:
                            temp = text[index+5:index + 12]
                            temp = temp.replace("\n", "")
                            temp = temp.strip()
                            edu_obj.gpa = temp
                            gpa_flag = False



                    # Find Date
                    if not date_flag:

                        # Remove GPA to avoid errors in finding date
                        while(True):
                            index = text.find("GPA")
                            if index >= 0:
                                temp = text[index:index+10]
                                text = text.replace(temp,"")
                            else:
                                break

                        matches = list(datefinder.find_dates(text))
                        edu_date = ""
                        if not matches == []:
                            currentYear = datetime.now().year
                            for temp_date in matches:
                                if not temp_date.year > currentYear + 4:
                                    edu_date += str(temp_date.month) + "/" + str(temp_date.year) + " - "
                            edu_obj.year = edu_date[:(len(edu_date) - 2)]
                            date_flag = True

                    if degree_flag:
                        break

                # When string match greater than equal to 95%
                if max_score >= 95:
                    break

    def get_shortlisted_keys(education_word_list, qualification_word_dict, university_word_dict):

        degree_list = ['associate','bachelor','bachelor\'s','masters', 'master', 'master\'s', 'doctoral']
        text_list = []
        date_flag, gpa_flag = False, False
        for k, lt_obj in text_prop_dict.iteritems():
            text = str(unicodedata.normalize('NFKD', lt_obj.get_text()).encode('utf-8'))
            flag = True

            # Search Education keyword
            for word in education_word_list:
                if word in text.lower():

                    # Search for university
                    for university, addr_list in university_word_dict.iteritems():
                        if str(university).lower() in text.lower():

                            edu_obj.university = university
                            edu_obj.set_addr(addr_list[0], addr_list[1], addr_list[2], "USA", addr_list[3])
                            degree_flag = False

                            # Search for degree
                            for degree in degree_list:
                                if degree.lower() in text.lower():
                                    degree_flag = search_major(text, degree, edu_obj)

                            # Search for degree if not found earlier
                            if not degree_flag:
                                search_major(text, degree, edu_obj)
                                for key, val in qualification_word_dict.iteritems():
                                    if key in text:
                                        edu_obj.degree = val
                                    if val in text and edu_obj.major == "":
                                        edu_obj.major =  val
                            # search_date(text, edu_obj)

                            # Find GPA
                            if not gpa_flag:
                                index = text.find("GPA")
                                if index >= 0:
                                    temp = text[index + 5:index + 12]
                                    temp = temp.replace("\n", "")
                                    temp = temp.strip()
                                    edu_obj.gpa = temp
                                    gpa_flag = False


                            # Find Date
                            if not date_flag:
                                # Remove GPA to avoid errors in finding date
                                while (True):
                                    index = text.find("GPA")
                                    if index >= 0:
                                        temp = text[index:index + 15]
                                        text = text.replace(temp, "")
                                    else:
                                        break

                                matches = list(datefinder.find_dates(text))
                                edu_date = ""
                                if not matches == []:
                                    currentYear = datetime.now().year
                                    for temp_date in matches:
                                        if not temp_date.year > currentYear + 4:
                                            edu_date += str(temp_date.month) + "/" + str(temp_date.year) + " - "
                                    edu_obj.year = edu_date[:(len(edu_date) - 2)]
                                    date_flag = True

                            flag = False
                            break

                    # Find closest neighbor
                    if flag:
                        flag = False
                        closest_neighbor(lt_obj,edu_obj,degree_list)

                    break

            if not flag:
                break

    education_word_list = get_education_word_list(dir_path)
    qualification_word_dict, abbr_list, degree_list = get_qualification_word_list(dir_path)
    university_word_dict = get_university_word_list(dir_path)
    major_word_list = get_major_word_list(dir_path)
    get_shortlisted_keys(education_word_list, qualification_word_dict, university_word_dict)


def display_list(obj_list):
    for lt_obj in obj_list:
        print lt_obj.__class__.__name__
        print(lt_obj.bbox, " ", type(lt_obj.bbox))
        print ("Height: ", lt_obj.height, " Width: ", lt_obj.width)
        print("Is Digit: ", lt_obj.get_text().isdigit(), "  Is Title: ", lt_obj.get_text().istitle(), "  Is Lower: ",
              lt_obj.get_text().islower())
        print(
            "Is Alnum: ", lt_obj.get_text().isalnum(), "  Is Identifier: ", lt_obj.get_text().find("+"), "  Is Space: ",
            lt_obj.get_text().isspace())
        print lt_obj.get_text()


def display():
    for k, v in text_dict.iteritems():
        lt_obj = text_prop_dict.get(k)
        print "Line No : ", k, "  Coordinate Box: ", lt_obj.bbox
        print "Text: ", [v]
        print ""


def display_list():

    for item in pdf_to_text_list:
        print item


def show_object(lt_obj):
    print lt_obj.__class__.__name__
    print(lt_obj.bbox)
    print ("Height: ", lt_obj.height, " Width: ", lt_obj.width)
    print("Is Digit: ", lt_obj.get_text().isdigit(), "  Is Title: ", lt_obj.get_text().istitle(), "  Is Lower: ",
          lt_obj.get_text().islower())
    print(
        "Is Alnum: ", lt_obj.get_text().isalnum(), "  Is Identifier: ", lt_obj.get_text().find("+"), "  Is Space: ",
        lt_obj.get_text().isspace())
    print lt_obj.get_text()


def parse_resume(key):
    global output_list_p1, output_list_p2, output_list_p3
    pdf_to_text_list = []
    text_list_p1 = []
    string_p1 = ""
    text_list_p2 = []
    string_p2 = ""
    text_list_p3 = []
    string_p3 = ""
    output_list_p1 = []
    output_list_p2 = []
    output_list_p3 = []

    con = connect_db()
    db = con.meteor
    fs = gridfs.GridFS(db)
    obj = fs.get(ObjectId(key))
    convert_pdf_to_txt(obj)
    read_pdf_miner(obj)
    create_segments()
    user = extract_user_detail()
    extract_education_detail(user)
    extract_work_exp_detail(user)


def connect_db():
    from pymongo import MongoClient
    con = MongoClient(host='127.0.0.1', port=3001)
    return con


def fetch_file_from_mongod():
    con = connect_db()
    db = con.meteor
    user_id_collection = db['user_id_mapping']

    cursor = user_id_collection.find()
    document_dict = cursor[0]
    for k,v in document_dict.iteritems():
        if not k == "_id":
            print "Resume: ", get_info(k)
            parse_resume(v)
            print "\n"


def get_info(key):
    global key_file_path
    reader = read_csv(key_file_path)
    for row in reader:
        if row[0] == key:
            return row[2]


def read_csv(input_file):
    """
    This function will read the csv file
    :param input_file: Name of the file
    :return:
    """

    file = open(input_file, 'r')
    reader = csv.reader(file)
    return reader


def write_csv_file(absolute_file_path, content_list, access_type):
    """
    This function will write post or campaign level metrics to the specified file

    Usage::

        >>> write_csv_file('Absolute_File_Path',[['valid','list'],[]],'a+')

    :param absolute_file_path:  The absolute path of output file
    :param content_list:        The metric list of list
    :param access_type:         It indicates type of access(write, append, etc.)
    :return:                    None

    """
    import csv
    try:
        with open(absolute_file_path, access_type) as file:
            wr = csv.writer(file)

            for row in content_list:
                wr.writerow(row)

    except Exception as e:
        raise e


def main():
    fetch_file_from_mongod()


if __name__ == '__main__':
    main()
