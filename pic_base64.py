
import base64
import glob


image_exts = ['gif', 'png', 'jpeg', 'jpg']
image_files = []


def main():
    for ext in image_exts:
        image_files.extend(glob.glob(f'*.{ext}'))
    print(image_files)


if __name__ == '__main__':
    main()

