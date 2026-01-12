# Getting set up
- To create an API key:
- Go to this site: https://aistudio.google.com/prompts/new_chat
- Click on “Get API Key” in the lower left
- Click on “+ Create API Key” in the top right of the page

This will generate an API Key unique to you that allows Gemini to talk with your device

Setting up Gemini CLI:
> [NOTE!]
> For this setup, you must have node.js installed (version 20 or higher), but we can still use the CLI to create python files (you don’t need to use javascript for your project). 

1. Find your terminal
- For macOS, search for “Terminal” in Launchpad
- For Windows, click the Start button or press the Windows key, then type "Windows Terminal" in the search bar and select the "Windows Terminal" application
- For Linux, use the keyboard shortcut Ctrl + Alt + T

2. Download node.js if you don’t already have it. You can find the installation package here.
- To double check that everything was installed correctly, use the terminal commands  “node -v”, which tells you the node.js version on your laptop, and “npm -v” to check the managing system version (as long as you don’t get a ‘command not found’ message, you should be good to go!)

3. To install the gemini CLI package globally, run the following command in terminal:
- For macOS and Linux users → `brew install gemini-cli`
- If you do not already have brew, go here, https://brew.sh/, and run the line on the website in your terminal and follow the instructions. 
- For Windows (or the other 2, you don’t have to use brew it’s just simpler) →
`npm install -g @google/gemini-cli`

4. Make sure to add the API Key (in the home directory or any project-specific file). To do this use the following command: `export GEMINI_API_KEY="YOUR_API_KEY"`
- Your API key is the one we found above. 
- Type `gemini` into the terminal.
- Type `2` and hit enter (to select “Use Gemini API Key”) if it is not already selected. If you correctly entered the API key before launching the CLI, it should automatically detect it and all you need to do is hit ‘enter’.
- Now you are ready to make your requests to Gemini!

> [!NOTE]
> This runs the gemini CLI in your home directory, but it could make sense to create a project-specific file to run it in. However, usually if you prompt it to create something for you, like an app, it will automatically make a project directory. The documentation can be found at this link. 