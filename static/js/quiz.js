// Quiz specific JavaScript

// Timer functionality
function startTimer(endTime, callback) {
    const timeDisplay = document.getElementById('time-display');
    const timeContainer = timeDisplay.parentElement;
    if (!timeDisplay) return;

    function updateTimer() {
        const now = new Date().getTime();
        const distance = endTime - now;
        
        if (distance <= 0) {
            clearInterval(timerInterval);
            timeDisplay.textContent = "00:00:00";
            timeContainer.style.color = 'red';
            if (typeof callback === 'function') callback();
            return;
        }
        
        // Calculate hours, minutes, and seconds
        const hours = Math.floor(distance / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        // Display in HH:MM:SS format (hide hours if 0)
        const timeString = hours > 0 
            ? `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
            : `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        timeDisplay.textContent = timeString;

        // Add blinking effect when < 10 minute remains
        if (distance < 600000) {
            timeContainer.style.color = 'red';
            timeDisplay.parentElement.classList.add('blinking');
        } else {
            timeContainer.style.color = 'green';
            timeDisplay.parentElement.classList.remove('blinking');
        }
    }

    // Initialize
    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
}

// Quiz creator functionality
function initQuizCreator() {
    const questionsContainer = document.getElementById('questions-container');
    const addQuestionBtn = document.getElementById('add-question');
    const questionCountInput = document.getElementById('question_count');
    
    if (!addQuestionBtn) return;
    
    let questionCount = 0;
    
    addQuestionBtn.addEventListener('click', function() {
        questionCount++;
        questionCountInput.value = questionCount;
        
        const questionDiv = document.createElement('div');
        questionDiv.className = 'question-container';
        questionDiv.id = `question-${questionCount}`;
        
        questionDiv.innerHTML = `
            <button type="button" class="remove-question" data-question="${questionCount}">&times;</button>
            <div class="form-group">
                <label for="question_${questionCount}_text">Question ${questionCount} Text:</label>
                <textarea id="question_${questionCount}_text" name="question_${questionCount}_text" required></textarea>
            </div>
            <div class="form-group">
                <label for="question_${questionCount}_type">Question Type:</label>
                <select id="question_${questionCount}_type" name="question_${questionCount}_type" required>
                    <option value="multiple">Multiple Choice</option>
                    <option value="text">Text Answer</option>
                </select>
            </div>
            <div class="choices-container" id="choices-${questionCount}">
                <!-- Choices will be added here -->
            </div>
            <input type="hidden" id="question_${questionCount}_choice_count" name="question_${questionCount}_choice_count" value="0">
            <button type="button" class="btn small add-choice" data-question="${questionCount}">Add Choice</button>
        `;
        
        questionsContainer.appendChild(questionDiv);
        
        // Add event listener to the new question's type selector
        const typeSelect = questionDiv.querySelector(`#question_${questionCount}_type`);
        typeSelect.addEventListener('change', function() {
            const choicesContainer = questionDiv.querySelector(`#choices-${questionCount}`);
            if (this.value === 'text') {
                choicesContainer.style.display = 'none';
                questionDiv.querySelector('.add-choice').style.display = 'none';
            } else {
                choicesContainer.style.display = 'block';
                questionDiv.querySelector('.add-choice').style.display = 'inline-block';
            }
        });
        
        // Trigger change event to set initial state
        typeSelect.dispatchEvent(new Event('change'));
        
        // Add event listener to the remove question button
        questionDiv.querySelector('.remove-question').addEventListener('click', function() {
            questionsContainer.removeChild(questionDiv);
            questionCountInput.value = parseInt(questionCountInput.value) - 1;
        });
        
        // Add event listener to the add choice button
        questionDiv.querySelector('.add-choice').addEventListener('click', function() {
            const questionNum = this.getAttribute('data-question');
            const choicesContainer = document.getElementById(`choices-${questionNum}`);
            const choiceCountInput = document.getElementById(`question_${questionNum}_choice_count`);
            
            let choiceCount = parseInt(choiceCountInput.value) + 1;
            choiceCountInput.value = choiceCount;
            
            const choiceDiv = document.createElement('div');
            choiceDiv.className = 'choice-container';
            
            choiceDiv.innerHTML = `
                <input type="text" id="question_${questionNum}_choice_${choiceCount}_text" 
                       name="question_${questionNum}_choice_${choiceCount}_text" 
                       placeholder="Choice text" required>
                <input type="checkbox" id="question_${questionNum}_choice_${choiceCount}_correct" 
                       name="question_${questionNum}_choice_${choiceCount}_correct" value="1">
                <label for="question_${questionNum}_choice_${choiceCount}_correct">Correct?</label>
                <button type="button" class="remove-choice" data-question="${questionNum}" data-choice="${choiceCount}">&times;</button>
            `;
            
            choicesContainer.appendChild(choiceDiv);
            
            // Add event listener to the remove choice button
            choiceDiv.querySelector('.remove-choice').addEventListener('click', function() {
                choicesContainer.removeChild(choiceDiv);
                choiceCountInput.value = parseInt(choiceCountInput.value) - 1;
            });
        });
    });
}

// Initialize quiz timer if on quiz page
if (document.getElementById('time-display')) {
    // Timer is initialized in the template with specific end time
}

// Initialize quiz creator if on create quiz page
if (document.getElementById('add-question')) {
    initQuizCreator();
}