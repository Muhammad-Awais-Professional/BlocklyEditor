document.addEventListener('DOMContentLoaded', () => {
    const connectButton = document.getElementById('connectWorldButton');
    const createCCButton = document.getElementById('createCCButton');
    const worldNameInput = document.getElementById('worldName');
    // Removed savesPathInput
    const connectionStatus = document.getElementById('connectionStatus');

    const computerIdSelect = document.getElementById('computerId');
    const refreshButton = document.getElementById('refreshButton'); 
    const runButton = document.getElementById('runButton');

    const copyButton = document.getElementById('copyButton');
    const downloadButton = document.getElementById('downloadButton');
    const downloadLuaButton = document.getElementById('downloadLuaButton');
    const loadButton = document.getElementById('loadButton');

    const modal = document.getElementById("modal");
    const closeButton = document.querySelector(".close-button");
    const modalMessage = document.getElementById("modalMessage");
    const saveSettingsButton = document.getElementById("saveSettingsButton");
    
    // Modal Functions
    function openModal(message, showSaveButton = false) {
        modal.style.display = "block";
        modalMessage.textContent = message;
        saveSettingsButton.style.display = showSaveButton ? "block" : "none";
    }

    closeButton.onclick = function () {
        modal.style.display = "none";
    }

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    saveSettingsButton.onclick = function () {
        modal.style.display = "none";
    }

    // Populate Computer IDs
    async function populateComputerIds() {
        try {
            const response = await fetch('/api/get_computer_ids');
            const result = await response.json();

            if (response.ok) {
                computerIdSelect.innerHTML = '<option value="" disabled selected>Select a Computer ID</option>';
                result.computer_ids.forEach(id => {
                    const option = document.createElement('option');
                    option.value = id;
                    option.textContent = id;
                    computerIdSelect.appendChild(option);
                });
            } else {
                openModal(result.message);
            }
        } catch (error) {
            console.error('Error fetching Computer IDs:', error);
            openModal('An error occurred while fetching Computer IDs.');
        }
    }

    // Connect to World
    async function connectToWorld() {
        const worldName = worldNameInput.value.trim();
        // Removed savesPath

        if (!worldName) {
            alert('Please enter a world name.');
            return;
        }

        connectionStatus.textContent = 'Connecting...';

        try {
            const payload = { 'world_name': worldName };
            // Removed saves_path from payload

            const response = await fetch('/api/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json();

            if (response.ok) {
                connectionStatus.textContent = result.message;

                if (!result.computercraft_installed) {
                    createCCButton.style.display = 'inline-block';
                } else {
                    createCCButton.style.display = 'none';
                }

                if (result.computercraft_installed) {
                    await populateComputerIds();
                }

            } else {
                connectionStatus.textContent = result.message;
                openModal(result.message);
            }
        } catch (error) {
            console.error('Error:', error);
            connectionStatus.textContent = 'An error occurred while connecting.';
            openModal('An error occurred while connecting to the world.');
        }
    }

    // Create ComputerCraft Folders
    async function createComputerCraft() {
        const worldName = worldNameInput.value.trim();
        // Removed savesPath

        if (!worldName) {
            alert('Please enter a world name.');
            return;
        }

        connectionStatus.textContent = 'Creating ComputerCraft folders...';

        try {
            const payload = { 'world_name': worldName };
            // Removed saves_path from payload

            const response = await fetch('/api/create_computercraft', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json();

            if (response.ok) {
                connectionStatus.textContent = result.message;
                createCCButton.style.display = 'none';
                
                await populateComputerIds();
            } else {
                connectionStatus.textContent = result.message;
                openModal(result.message);
            }
        } catch (error) {
            console.error('Error:', error);
            connectionStatus.textContent = 'An error occurred while creating ComputerCraft folders.';
            openModal('An error occurred while creating ComputerCraft folders.');
        }
    }

    // Run Program
    async function runProgram() {
        const computerId = computerIdSelect.value;
        if (!computerId) {
            alert('Please select a Computer ID.');
            return;
        }
    
        const code = document.getElementById('generatedCode').textContent.trim();
        if (!code) {
            alert('No Lua code generated to run.');
            return;
        }
    
        const fileName = document.getElementById('fileName').value.trim();
        if (!fileName) {
            alert('Please enter a program name.');
            return;
        }
    
        const sanitizedFileName = fileName.replace(/[^a-z0-9_\-]/gi, '_') + '.lua';
    
        try {
            const payload = {
                'computer_id': computerId,
                'code': code,
                'filename': sanitizedFileName
            };
    
            const response = await fetch('/api/run_program', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });
    
            const result = await response.json();
    
            if (response.ok) {
                alert(result.message);
            } else {
                alert(result.message);
            }
        } catch (error) {
            console.error('Error running program:', error);
            alert('An error occurred while running the program.');
        }
    }
    
    // Copy Code
    copyButton.addEventListener('click', () => {
        const code = document.getElementById('generatedCode').textContent.trim();
        if (!code) {
            alert('No code to copy.');
            return;
        }

        navigator.clipboard.writeText(code).then(() => {
            alert('Code copied to clipboard!');
        }).catch(err => {
            console.error('Could not copy text: ', err);
            alert('Failed to copy code.');
        });
    });

    // Download as TXT
    downloadButton.addEventListener('click', () => {
        const code = document.getElementById('generatedCode').textContent.trim();
        const fileNameInput = document.getElementById('fileName').value.trim();
        if (!code) {
            alert('No code to download.');
            return;
        }
        if (!fileNameInput) {
            alert('Please enter a program name.');
            return;
        }

        const sanitizedFileName = fileNameInput.replace(/[^a-z0-9_\-]/gi, '_');

        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${sanitizedFileName}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Download as Lua
    downloadLuaButton.addEventListener('click', () => {
        const code = document.getElementById('generatedCode').textContent.trim();
        const fileNameInput = document.getElementById('fileName').value.trim();
        if (!code) {
            alert('No Lua code generated to download.');
            return;
        }
        if (!fileNameInput) {
            alert('Please enter a program name.');
            return;
        }

        const sanitizedFileName = fileNameInput.replace(/[^a-z0-9_\-]/gi, '_');

        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${sanitizedFileName}.lua`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Load Lua or TXT File
    loadButton.addEventListener('click', () => {
        const loadFileInput = document.createElement('input');
        loadFileInput.type = 'file';
        loadFileInput.accept = '.lua,.txt';
        loadFileInput.onchange = (event) => {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const code = e.target.result;
                    document.getElementById('generatedCode').textContent = code;
                };
                reader.readAsText(file);
            }
        };
        loadFileInput.click();
    });

    // Refresh Computer IDs
    refreshButton.addEventListener('click', async () => {
        await populateComputerIds();
        alert('Computer IDs refreshed.');
    });

    // Event Listeners
    connectButton.addEventListener('click', connectToWorld);
    createCCButton.addEventListener('click', createComputerCraft);
    runButton.addEventListener('click', runProgram);
});
