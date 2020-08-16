
from google.cloud import vision
from google.cloud.vision import types
import io
from PIL import Image
from PIL import ImageDraw
from enum import Enum
import os
import time
import json
import shutil
import multiprocessing 
from gcv2hocr import generate_hocr
from hocr2pdf import export_pdf
from pdf2image import convert_from_path
from PyPDF2 import PdfFileMerger
import fitz


def pdf_checker(file_name):
    
    # checking if the file is fully scanned or has a percentage of text
    
    page_num = 0
    text_perc = 0.0

    
    doc = fitz.open(file_name)

    for page in doc:
        page_num = page_num + 1

        page_area = abs(page.rect)
        text_area = 0.0
        for b in page.getTextBlocks():
            r = fitz.Rect(b[:4]) # rectangle where block text appears
            text_area = text_area + abs(r)
        text_perc = text_perc + (text_area / page_area)

    text_perc = text_perc / page_num

    # If the percentage of text is very low, the document is most likely a scanned PDF
    if text_perc < 0.05:
        print("the file is scanned PDF")
        return True
    else:
        print("not fully scanned PDF - the file might be already searchable")
        stat = input('type y to continue n to cancel: ')
        if stat.lower() in 'yes':
            return True
        else:
            return False


def generate_json(img_file, json_path):
    
    #upload the img to gcv and save the result in json file 

    lang = [ 'de', 'en']

    client = vision.ImageAnnotatorClient()
    with io.open(img_file, 'rb') as image_file:
            content = image_file.read()
    content_image=types.Image(content=content)

    response=client.document_text_detection(image=content_image, image_context = {'language_hints' : lang})
    #response=client.text_detection(image=content_image, image_context = {'language_hints' : lang})
    annotation = response.text_annotations

    from google.protobuf.json_format import MessageToJson
    serialized = MessageToJson(response)

    with open(json_path, 'w') as f:
        f.write(serialized)

def gn_files(page):
    
    # generating json, hocr, for each page of the file
    img_name=(os.path.splitext(os.path.basename(page.filename))[0])
    img_path = os.path.join(path, f'{img_name}.jpg')
    json_path =os.path.join(path, f'{img_name}.json')
    hocr_path = os.path.join(path, f'{img_name}.hocr')
    page.save(img_path , 'JPEG')
    generate_json(img_path, json_path)
    generate_hocr(json_path, hocr_path)

    
    

def convert2pdf(file_name, defualt_dpi):
    
    print('generating path')
    base_file_name = os.path.splitext(os.path.basename(file_name))[0]
    global path
    path = os.path.join(os.getcwd(), base_file_name)
    try:
        os.makedirs(path)
    except OSError as error:  
        print(error) 


    if file_name.endswith('.jpg'):
        print('generating the pdf file, wait...')
        img_path = os.path.join(path, f'{base_file_name}.jpg')
        shutil.copy(file_name, img_path)

        json_path = os.path.join(path , f'{base_file_name}.json')
        generate_json(img_path, json_path)

        hocr_path = os.path.join(path , f'{base_file_name}.hocr')
        generate_hocr(json_path, hocr_path)

        pdf_path = os.path.join(os.getcwd() , f'output_{base_file_name}.pdf')
        export_pdf(path, pdf_path, defualt_dpi)
        print('the new file ' + f'output_{base_file_name}.pdf' + ' in the path ' + os.getcwd())

    elif file_name.endswith('.pdf'):
       
        if pdf_checker(file_name):
            print('generating the pdf file, wait...')
            images_from_path = convert_from_path(file_name, output_folder=path)

            for i, page in enumerate(images_from_path):
                gn_files(page)

            PROCESSES = multiprocessing.cpu_count() - 1
            
            with multiprocessing.Pool(PROCESSES) as proc:
                proc.map_async(gn_files,images_from_path)
                # clean up
                proc.close()
                proc.join()


            pdf_path = os.path.join(os.getcwd() , f'output_{base_file_name}.pdf')
            export_pdf(path, pdf_path, defualt_dpi)
            print('the new file ' + f'output_{base_file_name}.pdf' + ' in the path ' + os.getcwd())
           
        
    else: 
        print('unsupported file format ')

    #remove temp dir
    try:
        shutil.rmtree(path)
    except OSError as e:
        print("Error: %s : %s" % (path, e.strerror))

if __name__ == '__main__':
    
    #CREDENTIALS_file =''
    #os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= CREDENTIALS_file
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None:

        defualt_dpi = 300
        file_name  = 'file path'

        convert2pdf(file_name, defualt_dpi)
    else:
        raise EnvironmentError('GOOGLE_APPLICATION_CREDENTIALS environment variable needs to be set to import this module') from KeyError
