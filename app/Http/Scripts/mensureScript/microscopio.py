import sys
import argparse
from process_image_file import process_image_file


def parse_args_and_run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True, help='Caminho para o arquivo de imagem (png/jpg)')
    parser.add_argument('--anotacao', default='')
    parser.add_argument('--gemini_obs', default='')
    parser.add_argument('--cpf', default='')
    parser.add_argument('--user-id', default='')
    parser.add_argument('--user-name', default='')
    args = parser.parse_args()
    

    rc = process_image_file(args.image, args.anotacao, args.gemini_obs,
                             args.cpf,
                            args.user_id, args.user_name)
    sys.exit(rc)

if __name__ == '__main__':
    parse_args_and_run()
