import os
import sys
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



class TurboSx:
    def __init__(self, from_address, to, subject, body, pwd, smtp_server, smtp_port, smtp_con, mail_type="mail", body_type="html"):
        self.from_address = from_address
        self.to = to
        self.subject = subject
        self.body = body
        self.pwd = pwd
        self.mail_type = mail_type
        self.body_type = body_type
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_con = smtp_con
        self.send_mail()

    def display(self):
        print(self.from_address)

    def compose_mail(self):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = self.subject
        msg['From'] = self.from_address
        msg['To'] = self.to

        if self.body_type == "text":
            part = MIMEText(self.body, 'plain')
        elif self.body_type == "html":
            part = MIMEText(self.body, 'html')
        else:
            print("Error in loading Body Type!!!")

        msg.attach(part)
        return msg

    def send_mail(self):
        msg = self.compose_mail()

        try:
            self.smtp_con.login(self.from_address, self.pwd)
            self.smtp_con.sendmail(self.from_address, self.to, msg.as_string())
            self.smtp_con.quit()
        except Exception as e:
            print("Failed to send email:", e)


class ShootProcessor:
    def __init__(self, from_address, to_address, subject, body, pwd, smtp_server, smtp_port, smtp_con):
        self.from_address = from_address
        self.to_address = to_address
        self.subject = subject
        self.body = body
        self.pwd = pwd
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_con = smtp_con

    def send_email(self):
        turbo_sx = TurboSx(self.from_address, self.to_address, self.subject, self.body, self.pwd, self.smtp_server, self.smtp_port, self.smtp_con)

class FileProcessor:
    def __init__(self, inbound_path, outbound_path, builds_path):
        self.inbound_path = inbound_path
        self.outbound_path = outbound_path
        self.builds_path = builds_path
        
        if not os.path.exists(self.outbound_path):
            os.makedirs(self.outbound_path)

    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            return file.readlines()

    def write_file(self, file_path, content):
        with open(file_path, 'w') as file:
            file.write(content)

class ShootProcessor(FileProcessor):
    def __init__(self, inbound_path, outbound_path, builds_path):
        super().__init__(inbound_path, outbound_path, builds_path)

    def shoot(self):
        ls = os.listdir(self.inbound_path)
        t_count = len(ls)
        ndate = datetime.now().strftime("%Y%m%d")
        wpath_up = os.path.join(self.outbound_path, f"{ids}_{ndate}.csv")
        
        if len(ls) > 0:
            print("Total Files:", len(ls))
            f_count = 1
            for i in os.listdir(self.inbound_path):
                now = datetime.now()
                fpath = os.path.join(self.inbound_path, i)
                wpath = os.path.join(self.outbound_path, f"{ids}_{now.strftime('%H%M%S')}_{i}")
                wpath_f = os.path.join(self.outbound_path, f"fail_{now.strftime('%H%M%S')}_{i}")

                print("Preparing File " + str(f_count) + " of " + str(t_count))
                f_count += 1
                if i.endswith('.csv'):                    
                    print("File name: " + fpath)
                    file_content = self.read_file(fpath)
                    file_write = open(wpath, 'a+')
                    file_write_f = open(wpath_f, 'a+')
                    file_write_up = open(wpath_up, 'a+')
                    count = 0
                    fcount = 0
                    
                    for line in file_content:
                        if count == 0:
                            ln = line.strip().split(',')
                            try:
                                from_address = ln[0]
                                pwd = ln[1]
                                smtp_server = ln[2]
                                smtp_port = ln[3]
                                file_write.write(','.join(ln) + "\n")
                            except Exception as e:
                                print("Error in First line Configs for File {file}!!!".format(file=fpath))
                        else:
                            ln = line.strip().split(',')
                            print(count, end="::")
                            print(ln, end="")
                            subject = self.read_build_files(os.path.join(self.builds_path, "subject", ln[2])).format(name=ln[0])
                            body = self.read_build_files(os.path.join(self.builds_path, "body", ln[3])).replace("{name}", ln[0]).replace("{email}", ln[1])
                            try:
                                from_address = from_address
                                to_address = ln[1]
                                subject = subject
                                body = body
                                pwd = pwd
                                smtp_server = smtp_server
                                smtp_port = smtp_port
                                smtp_con = smtplib.SMTP(smtp_server, smtp_port)
                                smtp_con.starttls()
                                shoot_processor = ShootProcessor(from_address, to_address, subject, body, pwd, smtp_server, smtp_port, smtp_con)
                                shoot_processor.send_email()
                                print("-> Success", end=" : ")
                                print(smtp_server)
                                file_write.write(','.join(ln) + "\n")
                                file_write_up.write(','.join(ln) + "\n")
                            except Exception as e:
                                print("-> Fail ", end=" : ")
                                print(smtp_server, end=" \n ")
                                print(e)
                                fcount += 1
                                file_write_f.write(','.join(ln) + f",{smtp_server},{from_address}\n")
                        count += 1
                    file_write.close()
                    file_write_f.close()
                    file_write_up.close()
                    os.remove(fpath)
                    if fcount == 0:
                        os.remove(wpath_f)
                else:
                    print("Invalid File Extension " + i)
                    os.remove(fpath)
            ftpTransfer(self.outbound_path, f"{ids}_{ndate}.csv")
        else:
            print("No Files To Process in inbound")

    def read_build_files(self, path):
        with open(path, 'r') as file:
            return ''.join(file.readlines())

class SplitFeedsProcessor(FileProcessor):
    def __init__(self, feeds_path, inbound_path, outbound_path):
        super().__init__(inbound_path, outbound_path, None)
        self.feeds_path = feeds_path

    def split_feeds(self, record_limit):
        file_data = self.read_file(os.path.join(self.feeds_path, "data.csv"))
        file_email = self.read_file(os.path.join(self.feeds_path, "email.csv"))
        count = 0
        k = 0
        n = record_limit
        ls = file_email
        
        for line_data in file_data:
            if count % n == 0:
                curr_path = os.path.join(self.inbound_path, f"{count}_{datetime.now().strftime('%H%M%S')}_email.csv")
                file_write = open(curr_path, 'a+')
                file_write.write(ls[k].strip() + "\n")
                print(ls[k])
                ln = line_data.strip().split(',')
                file_write.write(','.join(ln) + "\n")
                k = (k + 1) % len(ls)
            else:
                file_write = open(curr_path, 'a+')
                ln = line_data.strip().split(',')
                file_write.write(','.join(ln) + "\n")
            count += 1
            file_write.close()

if __name__ == "__main__":
    usr = input("Enter User Name:")
    ids = input("Enter ID:")
    pwd = input("Enter Password:")
    code = '001'  # Assuming the code here
    
    try:
        if code == '001':    
            while True:
                print("Select Option:")
                print("Press 1 to Split Files (Feeds -> inbound):")
                print("Press 2 to Shoot (inbound -> outbound):")
                print("Press 3 to logout")
                val = input("Enter Option:")

                if val == "1":
                    print("Option 1")
                    feeds_path = sys.argv[1] + "\\feeds"
                    inbound_path = sys.argv[1] + "\\inbound"
                    outbound_path = sys.argv[1] + "\\outbound"
                    splitter = SplitFeedsProcessor(feeds_path, inbound_path, outbound_path)
                    record_limit = int(input("Enter The Data File Record Limit:"))
                    splitter.split_feeds(record_limit)
                elif val == "2":
                    print("Option 2")
                    inbound_path = sys.argv[1] + "\\inbound"
                    outbound_path = sys.argv[1] + "\\outbound"
                    builds_path = sys.argv[1] + "\\builds"
                    shooter = ShootProcessor(inbound_path, outbound_path, builds_path)
                    shooter.shoot()
                elif val == "3":
                    print("Option 3")
                    break
                else:
                    print("Invalid Selection")
        else:
            print("Error Code: " + code)
    except Exception as e:
        print(e)
