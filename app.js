// ========================================
// 健康與護理Ⅰ 線上測驗系統 - 應用程式邏輯
// ========================================

// Cookie helper functions
function setCookie(name, value, days = 14) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(JSON.stringify(value))}; expires=${expires}; path=/`;
}

function getCookie(name) {
    const cookie = document.cookie.split('; ').find(row => row.startsWith(name + '='));
    if (cookie) {
        try {
            return JSON.parse(decodeURIComponent(cookie.split('=')[1]));
        } catch {
            return null;
        }
    }
    return null;
}

class QuizApp {
    constructor() {
        this.questions = [];
        this.currentQuestionIndex = 0;
        this.answers = {};
        this.score = 0;
        this.mode = 'all';
        this.shuffleEnabled = true;
        this.immediateFeedback = true;
        this.selectedCount = 'all'; // 'all', 5, 10, 20, 30, 50
        this.selectedChapters = []; // Array of selected chapter IDs

        this.init();
    }

    init() {
        this.cacheDOM();
        this.bindEvents();
        this.addSVGGradient();
        this.populateChapters();
        this.loadPreferences();
    }

    cacheDOM() {
        // Screens
        this.startScreen = document.getElementById('start-screen');
        this.quizScreen = document.getElementById('quiz-screen');
        this.resultScreen = document.getElementById('result-screen');

        // Start screen elements
        this.shuffleCheckbox = document.getElementById('shuffle-questions');
        this.feedbackCheckbox = document.getElementById('show-immediate-feedback');
        this.btnStartAll = document.getElementById('btn-start-all');
        this.btnStartTF = document.getElementById('btn-start-tf');
        this.btnStartMC = document.getElementById('btn-start-mc');
        this.btnStartEssay = document.getElementById('btn-start-essay');
        this.btnStartImage = document.getElementById('btn-start-image');
        this.countButtons = document.querySelectorAll('.count-btn');
        this.chapterCheckboxes = document.getElementById('chapter-checkboxes');
        this.tfCountEl = document.getElementById('tf-count');
        this.mcCountEl = document.getElementById('mc-count');
        this.essayCountEl = document.getElementById('essay-count');

        // Quiz screen elements
        this.currentQuestionEl = document.getElementById('current-question');
        this.totalQuestionsEl = document.getElementById('total-questions');
        this.progressFill = document.getElementById('progress-fill');
        this.scoreDisplay = document.getElementById('score-display');
        this.questionType = document.getElementById('question-type');
        this.questionSource = document.getElementById('question-source');
        this.questionText = document.getElementById('question-text');
        this.optionsContainer = document.getElementById('options-container');
        this.feedbackSection = document.getElementById('feedback-section');
        this.feedbackContent = document.getElementById('feedback-content');
        this.btnHome = document.getElementById('btn-home');
        this.btnPrev = document.getElementById('btn-prev');
        this.btnNext = document.getElementById('btn-next');
        this.btnSubmit = document.getElementById('btn-submit');

        // Result screen elements
        this.resultIcon = document.getElementById('result-icon');
        this.scorePercent = document.getElementById('score-percent');
        this.scoreCircle = document.getElementById('score-circle');
        this.correctCount = document.getElementById('correct-count');
        this.wrongCount = document.getElementById('wrong-count');
        this.totalCount = document.getElementById('total-count');
        this.resultMessage = document.getElementById('result-message');
        this.btnReview = document.getElementById('btn-review');
        this.btnRetry = document.getElementById('btn-retry');
        this.reviewSection = document.getElementById('review-section');
        this.reviewList = document.getElementById('review-list');
    }

    bindEvents() {
        // Start buttons
        this.btnStartAll.addEventListener('click', () => this.startQuiz('all'));
        this.btnStartTF.addEventListener('click', () => this.startQuiz('tf'));
        this.btnStartMC.addEventListener('click', () => this.startQuiz('mc'));
        if (this.btnStartEssay) {
            this.btnStartEssay.addEventListener('click', () => this.startQuiz('essay'));
        }
        if (this.btnStartImage) {
            this.btnStartImage.addEventListener('click', () => this.startQuiz('image'));
        }

        // Count selection buttons
        this.countButtons.forEach(btn => {
            btn.addEventListener('click', () => this.selectCount(btn));
        });

        // Preference checkboxes
        this.shuffleCheckbox.addEventListener('change', () => this.savePreferences());
        this.feedbackCheckbox.addEventListener('change', () => this.savePreferences());

        // Chapter selection
        // Chapter checkbox events are bound in populateChapters

        // Navigation buttons
        this.btnHome.addEventListener('click', () => this.retryQuiz());
        this.btnPrev.addEventListener('click', () => this.navigateQuestion(-1));
        this.btnNext.addEventListener('click', () => this.navigateQuestion(1));
        this.btnSubmit.addEventListener('click', () => this.submitQuiz());

        // Result buttons
        this.btnReview.addEventListener('click', () => this.toggleReview());
        this.btnRetry.addEventListener('click', () => this.retryQuiz());
    }

    addSVGGradient() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '0');
        svg.setAttribute('height', '0');
        svg.innerHTML = `
      <defs>
        <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:#4f46e5;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#10b981;stop-opacity:1" />
        </linearGradient>
      </defs>
    `;
        document.body.appendChild(svg);
    }

    populateChapters() {
        // Populate chapter checkboxes
        this.chapterCheckboxes.innerHTML = '';

        quizData.chapters.forEach((chapter, index) => {
            const label = document.createElement('label');
            label.className = 'chapter-checkbox-label';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = chapter.id;
            checkbox.checked = true; // All chapters selected by default
            checkbox.addEventListener('change', () => this.onChapterChange());

            const checkmark = document.createElement('span');
            checkmark.className = 'checkmark';

            const text = document.createTextNode(chapter.shortName);

            label.appendChild(checkbox);
            label.appendChild(checkmark);
            label.appendChild(text);
            this.chapterCheckboxes.appendChild(label);
        });

        // Select all chapters by default
        this.selectedChapters = quizData.chapters.map(c => c.id);
        this.updateQuestionCounts();
    }

    onChapterChange() {
        const checkboxes = this.chapterCheckboxes.querySelectorAll('input[type="checkbox"]');
        this.selectedChapters = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        this.updateQuestionCounts();
        this.savePreferences();
    }

    loadPreferences() {
        const prefs = getCookie('quizPreferences');
        if (prefs) {
            // Load shuffle preference
            if (typeof prefs.shuffle === 'boolean') {
                this.shuffleCheckbox.checked = prefs.shuffle;
            }

            // Load immediate feedback preference
            if (typeof prefs.immediateFeedback === 'boolean') {
                this.feedbackCheckbox.checked = prefs.immediateFeedback;
            }

            // Load selected count preference
            if (prefs.selectedCount !== undefined) {
                this.selectedCount = prefs.selectedCount;
                this.countButtons.forEach(btn => {
                    btn.classList.remove('active');
                    const btnCount = btn.dataset.count === 'all' ? 'all' : parseInt(btn.dataset.count);
                    if (btnCount === prefs.selectedCount) {
                        btn.classList.add('active');
                    }
                });
            }

            // Load selected chapters preference
            if (Array.isArray(prefs.selectedChapters) && prefs.selectedChapters.length > 0) {
                this.selectedChapters = prefs.selectedChapters;
                const checkboxes = this.chapterCheckboxes.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(cb => {
                    cb.checked = prefs.selectedChapters.includes(cb.value);
                });
                this.updateQuestionCounts();
            }
        }
    }

    savePreferences() {
        const prefs = {
            shuffle: this.shuffleCheckbox.checked,
            immediateFeedback: this.feedbackCheckbox.checked,
            selectedCount: this.selectedCount,
            selectedChapters: this.selectedChapters
        };
        setCookie('quizPreferences', prefs);
    }

    updateQuestionCounts() {
        // Filter by selected chapters (multi-select)
        const chapterIds = this.selectedChapters;
        const tfCount = quizData.trueFalseQuestions.filter(q => chapterIds.includes(q.chapterId)).length;
        const mcCount = quizData.multipleChoiceQuestions.filter(q => chapterIds.includes(q.chapterId)).length;
        const essayCount = quizData.essayQuestions ? quizData.essayQuestions.filter(q => chapterIds.includes(q.chapterId)).length : 0;

        this.tfCountEl.textContent = tfCount;
        this.mcCountEl.textContent = mcCount;
        if (this.essayCountEl) {
            this.essayCountEl.textContent = essayCount;
        }
    }

    startQuiz(mode) {
        this.mode = mode;
        this.shuffleEnabled = this.shuffleCheckbox.checked;
        this.immediateFeedback = this.feedbackCheckbox.checked;
        this.answers = {};
        this.score = 0;
        this.currentQuestionIndex = 0;

        // Prepare questions based on mode
        this.prepareQuestions();

        // Switch to quiz screen
        this.switchScreen('quiz');
        this.renderQuestion();
    }

    prepareQuestions() {
        const chapterIds = this.selectedChapters;

        let tfQuestions = quizData.trueFalseQuestions
            .filter(q => chapterIds.includes(q.chapterId))
            .map(q => ({ ...q, type: 'tf' }));

        let mcQuestions = quizData.multipleChoiceQuestions
            .filter(q => chapterIds.includes(q.chapterId))
            .map(q => ({ ...q, type: 'mc' }));

        let essayQuestions = (quizData.essayQuestions || [])
            .filter(q => chapterIds.includes(q.chapterId))
            .map(q => ({ ...q, type: 'essay' }));

        switch (this.mode) {
            case 'tf':
                this.questions = [...tfQuestions];
                break;
            case 'mc':
                this.questions = [...mcQuestions];
                break;
            case 'essay':
                this.questions = [...essayQuestions];
                break;
            case 'image':
                // Use dedicated imageQuestions array
                let imageQuestions = (quizData.imageQuestions || [])
                    .filter(q => chapterIds.includes(q.chapterId));
                this.questions = [...imageQuestions];
                break;
            default:
                this.questions = [...tfQuestions, ...mcQuestions];
        }

        if (this.shuffleEnabled) {
            this.shuffleArray(this.questions);
        }

        // Limit questions based on selected count
        if (this.selectedCount !== 'all' && typeof this.selectedCount === 'number') {
            this.questions = this.questions.slice(0, this.selectedCount);
        }

        this.totalQuestionsEl.textContent = this.questions.length;
    }

    selectCount(btn) {
        // Remove active class from all buttons
        this.countButtons.forEach(b => b.classList.remove('active'));

        // Add active class to clicked button
        btn.classList.add('active');

        // Set selected count
        const countValue = btn.dataset.count;
        this.selectedCount = countValue === 'all' ? 'all' : parseInt(countValue);
        this.savePreferences();
    }

    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }

    renderQuestion() {
        const question = this.questions[this.currentQuestionIndex];
        const questionNum = this.currentQuestionIndex + 1;

        // Update progress
        this.currentQuestionEl.textContent = questionNum;
        this.progressFill.style.width = `${(questionNum / this.questions.length) * 100}%`;

        // Update score display
        const answeredCount = Object.keys(this.answers).length;
        if (answeredCount > 0) {
            this.scoreDisplay.textContent = `已答 ${answeredCount} 題`;
        } else {
            this.scoreDisplay.textContent = '';
        }

        // Update question info
        const typeNames = { 'tf': '是非題', 'mc': '選擇題', 'essay': '問答題' };
        this.questionType.textContent = typeNames[question.type] || '題目';
        this.questionSource.textContent = `出處：${question.source}`;

        // Use innerHTML to support embedded images/formatting in question text
        // Replace newlines with <br> if it's plain text, or just use as is
        if (question.question.includes('<')) {
            this.questionText.innerHTML = question.question;
        } else {
            this.questionText.innerHTML = question.question.replace(/\n/g, '<br>');
        }

        // Display image if question has one (legacy/single image support)
        let existingImg = this.questionText.parentElement.querySelector('.question-image');
        if (existingImg) {
            existingImg.remove();
        }
        if (question.image) {
            const img = document.createElement('img');
            img.src = question.image;
            img.className = 'question-image';
            img.alt = '題目圖片';
            img.style.maxWidth = '100%';
            img.style.marginTop = '1rem';
            img.style.borderRadius = '8px';
            this.questionText.parentElement.appendChild(img);
        }

        // Render options
        this.renderOptions(question);

        // Update navigation buttons
        this.updateNavButtons();

        // Reset feedback
        this.hideFeedback();

        // Show feedback if already answered and immediate feedback is on
        if (this.immediateFeedback && this.answers[this.currentQuestionIndex] !== undefined) {
            this.showFeedback(question);
        }
    }

    renderOptions(question) {
        this.optionsContainer.innerHTML = '';

        if (question.type === 'tf') {
            // True/False options
            const options = [
                { value: true, label: '○', text: '正確' },
                { value: false, label: '✗', text: '錯誤' }
            ];

            options.forEach(opt => {
                const optionEl = this.createOptionElement(opt.label, opt.text, opt.value, question, true);
                this.optionsContainer.appendChild(optionEl);
            });
        } else if (question.type === 'essay') {
            // Essay question - show reveal answer button and self-grading
            this.renderEssayOptions(question);
        } else {
            // Multiple choice options
            const letters = ['A', 'B', 'C', 'D'];
            question.options.forEach((option, index) => {
                const optionEl = this.createOptionElement(letters[index], option, index, question, false);
                this.optionsContainer.appendChild(optionEl);
            });
        }
    }

    renderEssayOptions(question) {
        const existingAnswer = this.answers[this.currentQuestionIndex];
        const answerRevealed = existingAnswer !== undefined;

        // Create container
        const container = document.createElement('div');
        container.className = 'essay-container';

        if (!answerRevealed) {
            // Show "reveal answer" button
            const revealBtn = document.createElement('button');
            revealBtn.className = 'essay-btn reveal-btn';
            revealBtn.innerHTML = '📖 顯示答案';
            revealBtn.addEventListener('click', () => this.revealEssayAnswer(question));
            container.appendChild(revealBtn);
        } else {
            // Show the answer
            const answerBox = document.createElement('div');
            answerBox.className = 'essay-answer-box';

            let answerContent = `<strong>參考答案：</strong><br>${(question.originalAnswer || question.answer).replace(/\n/g, '<br>')}`;

            if (question.answerImage) {
                answerContent += `<div class="answer-image-container"><img src="${question.answerImage}" alt="參考答案圖片" style="max-width: 100%; margin-top: 10px; border-radius: 4px;"></div>`;
            }

            answerBox.innerHTML = answerContent;
            container.appendChild(answerBox);

            // Show self-grading buttons if not yet graded
            if (existingAnswer === 'revealed') {
                const gradeContainer = document.createElement('div');
                gradeContainer.className = 'essay-grade-container';
                gradeContainer.innerHTML = '<p>請自評：你答對了嗎？</p>';

                const correctBtn = document.createElement('button');
                correctBtn.className = 'essay-btn correct-btn';
                correctBtn.innerHTML = '✓ 答對';
                correctBtn.addEventListener('click', () => this.gradeEssay(true, question));

                const wrongBtn = document.createElement('button');
                wrongBtn.className = 'essay-btn wrong-btn';
                wrongBtn.innerHTML = '✗ 答錯';
                wrongBtn.addEventListener('click', () => this.gradeEssay(false, question));

                gradeContainer.appendChild(correctBtn);
                gradeContainer.appendChild(wrongBtn);
                container.appendChild(gradeContainer);
            } else {
                // Already graded
                const resultBox = document.createElement('div');
                resultBox.className = `essay-result ${existingAnswer ? 'correct' : 'wrong'}`;
                resultBox.textContent = existingAnswer ? '✓ 自評：答對' : '✗ 自評：答錯';
                container.appendChild(resultBox);
            }
        }

        this.optionsContainer.appendChild(container);
    }

    revealEssayAnswer(question) {
        this.answers[this.currentQuestionIndex] = 'revealed';
        this.renderOptions(question);
        this.updateNavButtons();
    }

    gradeEssay(isCorrect, question) {
        this.answers[this.currentQuestionIndex] = isCorrect;
        // Store original answer text for display purposes before any modification
        if (!question.originalAnswer) {
            question.originalAnswer = question.answer;
        }
        this.renderOptions(question);
        this.updateNavButtons();

        // Auto-advance to next question after delay (same as regular questions)
        // Only if immediate feedback is enabled
        if (this.immediateFeedback) {
            const delay = isCorrect ? 1000 : 3000;
            const isLastQuestion = this.currentQuestionIndex === this.questions.length - 1;

            // Clear any existing timer
            if (this.autoAdvanceTimer) {
                clearTimeout(this.autoAdvanceTimer);
            }

            this.autoAdvanceTimer = setTimeout(() => {
                if (isLastQuestion) {
                    this.submitQuiz();
                } else {
                    this.navigateQuestion(1);
                }
            }, delay);
        }
    }

    createOptionElement(letter, text, value, question, isTF) {
        const div = document.createElement('div');
        div.className = `option-item${isTF ? ' tf-option' : ''}`;

        const letterSpan = document.createElement('span');
        letterSpan.className = 'option-letter';
        letterSpan.textContent = letter;

        const textSpan = document.createElement('span');
        textSpan.className = 'option-label-text';
        textSpan.textContent = text;

        div.appendChild(letterSpan);
        div.appendChild(textSpan);

        // Check if already answered
        const existingAnswer = this.answers[this.currentQuestionIndex];
        if (existingAnswer !== undefined && existingAnswer === value) {
            div.classList.add('selected');
        }

        // Apply correct/wrong styling if feedback is shown
        if (this.immediateFeedback && existingAnswer !== undefined) {
            div.classList.add('disabled');
            if (value === question.answer) {
                div.classList.add('correct');
            } else if (existingAnswer === value) {
                div.classList.add('wrong');
            }
        }

        // Add click handler
        div.addEventListener('click', () => this.selectOption(value, question));

        return div;
    }

    selectOption(value, question) {
        // Don't allow re-selection if immediate feedback is on and already answered
        if (this.immediateFeedback && this.answers[this.currentQuestionIndex] !== undefined) {
            return;
        }

        this.answers[this.currentQuestionIndex] = value;

        // Re-render options to show selection
        this.renderOptions(question);

        // Show immediate feedback if enabled
        if (this.immediateFeedback) {
            this.showFeedback(question);
        }

        // Update nav buttons
        this.updateNavButtons();
    }

    showFeedback(question) {
        const userAnswer = this.answers[this.currentQuestionIndex];
        const isCorrect = userAnswer === question.answer;

        this.feedbackSection.classList.remove('correct', 'wrong');
        this.feedbackSection.classList.add(isCorrect ? 'correct' : 'wrong');
        this.feedbackSection.style.display = 'block';

        let feedbackHTML = '';
        if (isCorrect) {
            feedbackHTML = '<strong>✓ 答對了！</strong>';
        } else {
            if (question.type === 'tf') {
                feedbackHTML = `<strong>✗ 答錯了</strong><br>正確答案：${question.answer ? '○ 正確' : '✗ 錯誤'}`;
            } else {
                const letters = ['A', 'B', 'C', 'D'];
                feedbackHTML = `<strong>✗ 答錯了</strong><br>正確答案：(${letters[question.answer]}) ${question.options[question.answer]}`;
            }
        }

        if (question.explanation) {
            feedbackHTML += `<br><br><em>解析：${question.explanation}</em>`;
        }

        this.feedbackContent.innerHTML = feedbackHTML;

        // Mark options as correct/wrong
        const options = this.optionsContainer.querySelectorAll('.option-item');
        options.forEach(opt => {
            opt.classList.add('disabled');
        });

        // Auto-advance to next question after delay
        // 1 second for correct answers, 3 seconds for wrong answers
        const delay = isCorrect ? 1000 : 3000;
        const isLastQuestion = this.currentQuestionIndex === this.questions.length - 1;

        // Clear any existing timer
        if (this.autoAdvanceTimer) {
            clearTimeout(this.autoAdvanceTimer);
        }

        this.autoAdvanceTimer = setTimeout(() => {
            if (isLastQuestion) {
                this.submitQuiz();
            } else {
                this.navigateQuestion(1);
            }
        }, delay);
    }

    hideFeedback() {
        this.feedbackSection.style.display = 'none';
        this.feedbackSection.classList.remove('correct', 'wrong');
    }

    updateNavButtons() {
        // Previous button
        this.btnPrev.disabled = this.currentQuestionIndex === 0;

        // Next/Submit button
        const isLastQuestion = this.currentQuestionIndex === this.questions.length - 1;
        const answer = this.answers[this.currentQuestionIndex];
        // For essay, must be graded (true/false), not just 'revealed'
        const hasAnswer = answer !== undefined && answer !== 'revealed';

        if (isLastQuestion) {
            this.btnNext.style.display = 'none';
            this.btnSubmit.style.display = 'block';

            // Enable submit only if current question is answered
            this.btnSubmit.disabled = !hasAnswer;
        } else {
            this.btnNext.style.display = 'block';
            this.btnSubmit.style.display = 'none';

            // Enable next only if current question is answered
            this.btnNext.disabled = !hasAnswer;
        }
    }

    navigateQuestion(direction) {
        const newIndex = this.currentQuestionIndex + direction;

        if (newIndex >= 0 && newIndex < this.questions.length) {
            this.currentQuestionIndex = newIndex;
            this.renderQuestion();
        }
    }

    submitQuiz() {
        // Calculate score
        this.score = 0;
        this.questions.forEach((question, index) => {
            const userAnswer = this.answers[index];
            // For essay questions, user grades themselves (true = correct, false = wrong)
            if (question.type === 'essay') {
                if (userAnswer === true) {
                    this.score++;
                }
            } else if (userAnswer === question.answer) {
                this.score++;
            }
        });

        // Switch to result screen
        this.switchScreen('result');
        this.renderResult();
    }

    renderResult() {
        const total = this.questions.length;
        const correct = this.score;
        const wrong = total - correct;
        const percent = Math.round((correct / total) * 100);

        // Update stats
        this.correctCount.textContent = correct;
        this.wrongCount.textContent = wrong;
        this.totalCount.textContent = total;

        // Animate score circle
        setTimeout(() => {
            const circumference = 2 * Math.PI * 45;
            const offset = circumference - (percent / 100) * circumference;
            this.scoreCircle.style.strokeDashoffset = offset;
        }, 100);

        // Animate score number
        this.animateNumber(this.scorePercent, 0, percent, 1500);

        // Result icon and message
        if (percent >= 90) {
            this.resultIcon.textContent = '🏆';
            this.resultMessage.textContent = '太棒了！你對健康知識的掌握非常優秀！';
        } else if (percent >= 70) {
            this.resultIcon.textContent = '🎉';
            this.resultMessage.textContent = '做得好！你已經掌握了大部分的健康概念。';
        } else if (percent >= 60) {
            this.resultIcon.textContent = '👍';
            this.resultMessage.textContent = '不錯！建議再複習一下答錯的題目。';
        } else {
            this.resultIcon.textContent = '📚';
            this.resultMessage.textContent = '需要多加努力！建議重新複習課本內容。';
        }

        // Reset review section
        this.reviewSection.style.display = 'none';
        this.reviewList.innerHTML = '';
    }

    animateNumber(element, start, end, duration) {
        const startTime = performance.now();

        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOut = 1 - Math.pow(1 - progress, 3);

            const current = Math.round(start + (end - start) * easeOut);
            element.textContent = current;

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };

        requestAnimationFrame(step);
    }

    toggleReview() {
        if (this.reviewSection.style.display === 'none') {
            this.renderReview();
            this.reviewSection.style.display = 'block';
            this.btnReview.textContent = '📋 隱藏詳細答案';
        } else {
            this.reviewSection.style.display = 'none';
            this.btnReview.textContent = '📋 檢視詳細答案';
        }
    }

    renderReview() {
        this.reviewList.innerHTML = '';

        this.questions.forEach((question, index) => {
            const userAnswer = this.answers[index];
            const isCorrect = userAnswer === question.answer;

            const item = document.createElement('div');
            item.className = `review-item ${isCorrect ? 'correct' : 'wrong'}`;

            let userAnswerText, correctAnswerText;

            if (question.type === 'tf') {
                userAnswerText = userAnswer ? '○ 正確' : '✗ 錯誤';
                correctAnswerText = question.answer ? '○ 正確' : '✗ 錯誤';
            } else {
                const letters = ['A', 'B', 'C', 'D'];
                userAnswerText = `(${letters[userAnswer]}) ${question.options[userAnswer]}`;
                correctAnswerText = `(${letters[question.answer]}) ${question.options[question.answer]}`;
            }

            let html = `
        <div class="review-question">
          <strong>${index + 1}.</strong> ${question.question}
        </div>
        <div class="review-answer">
          <span class="your-answer">你的答案：${userAnswerText}</span>
          ${!isCorrect ? `<span class="correct-answer">正確答案：${correctAnswerText}</span>` : ''}
        </div>
      `;

            if (question.explanation) {
                html += `<div class="review-explanation">💡 ${question.explanation}</div>`;
            }

            item.innerHTML = html;
            this.reviewList.appendChild(item);
        });
    }

    retryQuiz() {
        this.switchScreen('start');
        this.reviewSection.style.display = 'none';
    }

    switchScreen(screenName) {
        // Hide all screens
        [this.startScreen, this.quizScreen, this.resultScreen].forEach(screen => {
            screen.classList.remove('active');
        });

        // Show target screen
        switch (screenName) {
            case 'start':
                this.startScreen.classList.add('active');
                break;
            case 'quiz':
                this.quizScreen.classList.add('active');
                break;
            case 'result':
                this.resultScreen.classList.add('active');
                break;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new QuizApp();
});
