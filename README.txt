Vraudrak's ngrok Site Server - Usage Instructions
-----------------------------------

Folder Structure:

/<SERVER_FOLDER>
  /DOCS             <- All site files go here (index.html, uploads, etc.)
  CONFIG            <- Store ngrok token and future configs
  server.py         <- Main server script
  TODO.txt          <- Optional: features to implement

-----------------------------------
How to Run the Server:

1) Open a terminal and navigate to the folder containing server.py:
   cd /path/to/<SERVER_FOLDER>

2) Make sure Python 3 is installed:
   python3 --version
   (If not installed, install Python 3 for your OS.)

3) Optional: Configure ngrok for public access:
   - Download ngrok from https://ngrok.com/download
   - Create or edit CONFIG
   - Add your ngrok authtoken:
     NGROK_AUTHTOKEN=YOUR_NGROK_AUTHTOKEN
   - If ngrok is configured, the script will start a public tunnel automatically.

4) Start the server:
   python3 server.py

5) Output:
   - Local URL: The script will print the local address, e.g., http://127.0.0.1:PORT
   - Public URL: If ngrok is configured, the public ngrok URL will be displayed.

6) Stop the server:
   Press Ctrl+C in the terminal to stop the Python server.
   If ngrok is running, it will terminate automatically.

-----------------------------------
Notes:

- All site files should go inside the DOCS folder.  
- Uploads or future password-protected storage can be added inside DOCS/uploads/.  
- User accounts and other configs can be stored in CONFIG.  
- The script automatically detects its folder location, so it can run from **any folder or drive**.  
- Always back up CONFIG to keep ngrok token and other settings safe.
