function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (message === ""){
    popup("Please Enter Something", "blue", "3s");
    return;
  } 
    

  addMessage("user", message);
  input.value = "";

  // Add bot loading message
  const loadingId = "loading-" + Date.now();
  addMessage("bot", "Thinking...", loadingId, true);

  // Simulate bot thinking
  const formData = new FormData();
  formData.append("message", message);
  popup("request send successfully", "green", "3s");
  $.ajax({
    url: "/chatCore",
    type: "POST",
    data: formData,
    processData: false,
    contentType: false,
    success: function (data) {
    //   console.log("Response from server:", data);
      const reply = data.reply || "🤖 Sorry, no comments.";
      removeMessage(loadingId);
      addMessage("bot", reply);
    },
    error: function (xhr, status, error) {
      popup("request send failed", "red", "3s");
      console.error("Error:", error, status, xhr);
      removeMessage(loadingId);
      addMessage("bot", xhr.responseJSON.reply||"⚠️ Error reaching chat server.");
    },
  });
}

function formatGeminiText(text) {
  let formattedText = '';
  let openTag = false;
  let insideCodeBlock = false;
  let headingLevel = 0;

  const lines = text.split('\n'); // Split the text into lines

  lines.forEach(line => {
      headingLevel = 0;
      if (line.startsWith('---')) {
          formattedText += '<hr style="margin: 10px 0; border: 1px solid #ccc;"><br>'; // Horizontal rule
          return; // Skip to the next line
      }

      // Check for headings (up to level 3)
      if (line.startsWith('# ')) {
          headingLevel = 1;
      } else if (line.startsWith('## ')) {
          headingLevel = 2;
      } else if (line.startsWith('### ')) {
          headingLevel = 3;
      }

      if (headingLevel > 0)
      {
          const headingText = line.substring(headingLevel + 1);
          formattedText += `<h${headingLevel} style="margin: 10px 0; font-weight: bold; font-size: ${24 - (headingLevel -1) * 2}px;">${headingText}</h${headingLevel}><br>`;
          return;
      }

      for (let i = 0; i < line.length; i++) {
          const char = line[i];
          const nextChars = line.substring(i, i + 3); // Check next 3 chars

          if (nextChars === '```') {
              if (insideCodeBlock) {
                  formattedText += '</code><br>';
                  insideCodeBlock = false;
                  i += 2; // Skip the rest of the backticks
              } else {
                  formattedText += '<code style="background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; display: block; white-space: pre-wrap; font-family: monospace; margin: 10px 0;">';
                  insideCodeBlock = true;
                  i += 2;
              }
          } else if (!insideCodeBlock) { // Only apply formatting outside code blocks
              if (char === '*') {
                  if (openTag) {
                      formattedText += '</span>';
                      openTag = false;
                  } else {
                      formattedText += '<span style="font-weight: bold;">';
                      openTag = true;
                  }
              } else if (char === '_') {
                  if (openTag) {
                      formattedText += '</span>';
                      openTag = false;
                  } else {
                      formattedText += '<span style="font-style: italic;">';
                      openTag = true;
                  }
              } else if (char === '~') {
                  if (openTag) {
                      formattedText += '</span>';
                      openTag = false;
                  } else {
                      formattedText += '<span style="text-decoration: line-through;">';
                      openTag = true;
                  }
               } else {
                  formattedText += char;
              }
          } else {
              formattedText += char; // Inside code block, add raw text
          }
      }
      formattedText += '<br>';
  });

  // Close any open tags at the end
  if (openTag) {
      formattedText += '</span>';
  }
  return formattedText;
}

function addMessage(sender, text, id = null, isLoading = false) {
  const chatBox = document.getElementById("chat-box");
  const messageDiv = document.createElement("div");
  messageDiv.className = `chat-message ${sender}-message`;
  if (id) messageDiv.id = id;

  if (isLoading) {
    messageDiv.innerHTML = `<span class="dot-loader"></span> <span>${text}</span>`;
  } else {
    text = formatGeminiText(text);
    messageDiv.innerHTML = text;
  }

  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function removeMessage(id) {
  const msg = document.getElementById(id);
  if (msg) msg.remove();
}

function getBotResponse(message) {
  // Replace with real logic or API call
  return `You said: "${message}"`;
}

document.getElementById("user-input").addEventListener("keydown", function (e) {
  if (e.key === "Enter") sendMessage();
});
