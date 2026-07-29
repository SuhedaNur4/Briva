import zipfile

def main():
    try:
        with zipfile.ZipFile('Briva-sprint3-gamification.zip', 'r') as zf:
            files = zf.namelist()
            with open('zip_contents.txt', 'w', encoding='utf-8') as f:
                for filename in files:
                    f.write(filename + '\n')
    except Exception as e:
        with open('zip_contents.txt', 'w', encoding='utf-8') as f:
            f.write(f"Error: {e}")

if __name__ == '__main__':
    main()
