import qrcode

def generate_qr(data, filename):

    qr = qrcode.make(data)

    file_path = f"data/{filename}.png"
    qr.save(file_path)

    return file_path