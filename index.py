
import os
from generate_pdf import convert2pdf


if __name__ == '__main__':
    
    CREDENTIALS_file =''
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= CREDENTIALS_file
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None:

        defualt_dpi = 300
        file_name  = 'file path'

        convert2pdf(file_name, defualt_dpi)
    else:
        raise EnvironmentError('GOOGLE_APPLICATION_CREDENTIALS environment variable needs to be set to import this module') from KeyError
