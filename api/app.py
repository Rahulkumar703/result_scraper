from flask import Flask, request, send_file, Response, render_template,stream_with_context
import os
import logging
from scrape import save_results_to_excel

app = Flask(__name__,template_folder='../templates')

# Constants
BRANCHES = {"CSE": 105, "CIVIL": 101, "MECH": 102, "EEE": 110, "AI": 115, "CA": 119}

URL = [
    {
        "batch": 2021,
        "semester": 1,
        "link": "https://results.akuexam.net/ResultsBTechBPharm1stSemPub2021.aspx?Sem=I&RegNo="
    },
    {
        "batch": 2021,
        "semester": 2,
        "link": "https://results.akuexam.net/ResultsBTechBPharm2ndSemPub2022.aspx?Sem=II&RegNo="
    }
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Logs to console
        logging.FileHandler("app.log")  # Logs to a file
    ]
)

def clear_log_file():
    with open("app.log", 'w') as file:
        # Opening in 'w' mode clears the file
        pass

@app.route("/logs", methods=["GET"])
def get_logs():
    log_file = "app.log"
    
    def generate_log_lines():
        with open(log_file, "r") as file:
            # Move the file pointer to the end of the file
            file.seek(0, 2)
            while True:
                line = file.readline()
                if not line:
                    time.sleep(0.1)  # Sleep briefly to prevent busy waiting
                    continue
                yield line

    return Response(stream_with_context(generate_log_lines()), mimetype='text/plain')

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/aku", methods=["GET", "POST"])
def aku():
    if request.method == "POST":
        batch = request.form.get("batch")
        semester = request.form.get("semester")
        branch = request.form.get("branch")

        clear_log_file()

        # Convert batch to integer
        try:
            batch_int = int(batch)
        except ValueError:
            return "Batch number must be an integer", 400
        
        # Validate branch
        if branch not in BRANCHES:
            return "Invalid branch name", 400
        
        # Validate semester and batch
        url_entry = next((entry for entry in URL if entry["batch"] == batch_int and entry["semester"] == int(semester)), None)
        if url_entry is None:
            return "Invalid batch or semester", 400

        branch_code = BRANCHES[branch]
        batch_code = batch_int % 100
        REG_START = f"{batch_code:02d}{branch_code}1130"
        output_file = f"results/{branch}_{batch}_SEM-{semester}.xlsx"
        url = f"{url_entry['link']}"

        # Check if the file already exists
        if os.path.exists(output_file):
            return send_file(output_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True)
        
        # Generate the file
        app.logger.info(f"Generating file from URL: {url}")
        reg_no_list = [f"{REG_START}{i:02d}" for i in range(1, 66)]
        save_results_to_excel(url, reg_no_list, output_file)
        return send_file(output_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True)

    return render_template("aku.html")



def remove_registration_number(url):
    # Find the start of the registration number
    reg_start_index = url.find('RegNo=')
    if reg_start_index == -1:
        # If 'RegNo=' is not found, return the URL as is
        return url
    
    # Find the end of the registration number
    reg_end_index = url.find('&', reg_start_index)
    
    if reg_end_index == -1:
        # If there's no '&' after 'RegNo=', it means 'RegNo=' is the end of the URL
        return url[:reg_start_index + len('RegNo=')]
    
    # Return the URL with the registration number removed
    return url[:reg_start_index + len('RegNo=')] + url[reg_end_index:]



@app.route("/beu", methods=["GET", "POST"])
def beu():
    if request.method == "POST":
        batch = request.form.get("batch")
        semester = request.form.get("semester")
        branch = request.form.get("branch")
        url = request.form.get("url")

        clear_log_file()

        # Convert batch to integer
        try:
            batch_int = int(batch)
        except ValueError:
            return "Batch number must be an integer", 400
        
        # Validate branch
        if branch not in BRANCHES:
            return "Invalid branch name", 400
        
        print(url)

        branch_code = BRANCHES[branch]
        batch_code = batch_int % 100
        output_file = f"results/{branch}_{batch}_SEM-{semester}.xlsx"
        url = remove_registration_number(url)
        REG_START_original=f"{batch_code:02d}{branch_code}113"
        # Check if the file already exists
        # if os.path.exists(output_file):
        #     return send_file(output_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True)
        
        # Generate the file
        app.logger.info(f"Generating file from URL: {url}")
        if int(semester) >= 3:
            incremented_batch_code = batch_code + 1
            REG_START = f"{incremented_batch_code:02d}{branch_code}113"
            reg_no_list = [f"{REG_START_original}{i:03d}" for i in range(1, 66)] + [f"{REG_START}{i:03d}" for i in range(901, 926)]
        else:
            REG_START = f"{batch_code:02d}{branch_code}113"
            reg_no_list = [f"{REG_START}{i:03d}" for i in range(1, 66)]

        save_results_to_excel(url, reg_no_list, output_file)


        return send_file(output_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True)

    return render_template("beu.html")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
