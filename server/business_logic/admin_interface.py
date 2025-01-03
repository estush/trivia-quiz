from data.database_functions_quizes import (
    create_quiz,
    get_quiz,
    update_quiz,
    delete_quiz,
    create_question,
    get_user,
    get_questions,
    generate_unique_question_id,
    generate_unique_quiz_id,
    create_option,
    get_participant_answers,
    get_current_question,
    get_quizzes_by_user,
    get_all_participants,
    get_question,
    get_options_by_question
    
)
import time
import sqlite3
import os

import sqlite3

DB_NAME = 'quizzes_data.db'


def create_new_quiz(title, user_id, questions):
    """
    Creates a new quiz with questions and single correct answer.
    """
    if not all([title, user_id, questions]):
        return {'error': 'Title, user ID, and questions are required.'}, 400

    try:
        quiz_id = generate_unique_quiz_id()
        create_quiz(quiz_id, title, user_id)
        add_questions_to_quiz(quiz_id, questions)
        return {'message': 'Quiz created successfully.', 'quiz_id': quiz_id}, 201
    except Exception as e:
        print("Error in create_new_quiz:", e)
        return {'error': 'Error creating quiz.'}, 500


def add_questions_to_quiz(quiz_id, questions):
    """
    Adds questions to a quiz.
    """
    for question in questions:
        q_text = question.get('question')
        answers = question.get('answers')
        correct_option = question.get('correctAnswer')

        if not all([q_text, answers, correct_option is not None]):
            raise ValueError('Each question must have text, answers, and a correct answer.')

        question_id = generate_unique_question_id()
        create_question(question_id, quiz_id, q_text)
        add_options_to_question(question_id, answers, correct_option)


def add_options_to_question(question_id, answers, correct_option):
    """
    Adds options to a question.
    """
    for idx, answer_text in enumerate(answers, start=1):
        create_option(question_id, answer_text, idx == correct_option)


def view_quizzes(user_id):
    """
    Retrieves all quizzes created by a user.
    """
    user = get_user(user_id)
    if not user:
        return {'error': 'User not found.'}, 404
    try:
        quizzes = get_quizzes_by_user(user_id)
        return {'quizzes': quizzes}, 200
    except Exception as e:
        return {'error': 'שגיאה בשרת.'}, 500
    

def edit_quiz(quiz_id, user_id, name=None, questions=None):
    """
    Edits an existing quiz's details and questions.
    """
    quiz = get_quiz(quiz_id)
    if not quiz:
        return {'error': 'Quiz not found.'}, 404
    update_quiz(quiz_id, name=name)
    if questions:
        for question in questions:
            q_text = question.get('question_text')
            options = question.get('options')
            correct_options = question.get('correct_options')  # List of correct option indices
            question_id = generate_unique_question_id()
            create_question(question_id, quiz_id, q_text)
            for idx, option_text in enumerate(options, start=1):
                is_correct = idx in correct_options
                create_option(question_id, option_text, is_correct)
    return {'message': 'Quiz updated successfully.'}, 200

def activate_quiz(quiz_id: str, user_id: str) -> tuple[dict, int]:
    """
    Activates a quiz.
    """
    try:
        quiz = get_quiz(quiz_id)
        if not quiz:
            return {'error': 'Quiz not found.'}, 404

        quiz_questions = get_questions(quiz_id)

        if not quiz_questions or len(quiz_questions) < 1:
            return {'error': 'Quiz must have at least one question.'}, 400

        first_question_id = quiz_questions[0].get('id')

        update_quiz(
            id=quiz_id,
            status='active',
            current_question_id=first_question_id,
            question_start_time=int(time.time())
        )

        return {'message': 'Quiz activated successfully.'}, 200
    except Exception as e:
        return {'error': 'שגיאה בשרת.'}, 500

def go_to_next_question(quiz_id):
    """
    Moves the quiz to the next question.
    """
    quiz = get_quiz(quiz_id)
    if not quiz:
        return {'error': 'Quiz not found.', 'status': 'inactive'}, 404

    quiz_questions = get_questions(quiz_id)
    if not quiz_questions:
        return {'error': 'No questions found for this quiz.', 'status': 'inactive'}, 404

    current_question_id = quiz.get('current_question_id')
    if not current_question_id:
        return {'error': 'No active question for this quiz.', 'status': 'inactive'}, 400

    return move_to_next_question(quiz_id, quiz_questions, current_question_id)


def move_to_next_question(quiz_id, quiz_questions, current_question_id):
    """
    Helper function to move to the next question.
    """
    question_ids = [q.get('id') for q in quiz_questions]
    current_question_index = question_ids.index(current_question_id)

    if current_question_index == len(question_ids) - 1:
        update_quiz(quiz_id, status='completed')
        return {'message': 'Quiz completed.', 'status': 'completed'}, 200

    next_question_id = question_ids[current_question_index + 1]
    update_quiz(quiz_id, current_question_id=next_question_id, question_start_time=int(time.time()))
    return {'message': 'Moved to next question.', 'status': 'active'}, 200


def get_quiz_statistics(quiz_id: str, user_id: str) -> tuple:
    """
    Retrieves statistics for a given quiz, including participants and their answers.

    :param quiz_id: מזהה החידון.
    :param user_id: מזהה המשתמש המבקש את הסטטיסטיקות.
    :return: Tuple עם מילון סטטיסטיקות וקוד סטטוס HTTP.
    """
    try:
        participants = get_all_participants(quiz_id)  # קריאה לפונקציה הנכונה
        quiz = get_quiz(quiz_id)

        if not quiz:
            return {'error': 'חידון לא נמצא.'}, 404

        statistics = {
            'quiz_id': quiz_id,
            'title': quiz.get('name'),
            'status': quiz.get('status'),
            'participants_count': len(participants),
            'participants': participants
        }

        return {'statistics': statistics}, 200

    except sqlite3.Error as e:
        return {'error': 'שגיאה במסד הנתונים.'}, 500

    except Exception as e:
        print("Error in get_quiz_statistics:", e)
        return {'error': 'שגיאה בשרת.'}, 500
    

def get_participants(quiz_id):
    """
    Retrieves all participants for a given quiz.
    """
    quiz = get_quiz(quiz_id)
    if not quiz:
        return {'error': 'Quiz not found.'}, 404
    participants = get_all_participants(quiz_id)
    return {'participants': participants}, 200

    

def calculate_score(answers):
    """
    Calculates the score based on participant's answers.
    """
    score = 0
    first_correct = {}
    ordered_answers = sorted(answers, key=lambda x: x['time_taken'])

    for answer in ordered_answers:
        if answer['is_correct']:
            score += 10
            q_id = answer['question_id']
            if q_id not in first_correct:
                first_correct[q_id] = 1
                score += 10
            elif first_correct[q_id] < 3:
                first_correct[q_id] += 1
                score += 5
    return score


def get_user_by_id(user_id):
    """
    Retrieves a user by ID.
    """
    return get_user(user_id), 200


def get_current_active_question(quiz_id):
    """
    Retrieves the current active question for a quiz.
    """
    quiz = get_quiz(quiz_id)
    if not quiz:
        return {'error': 'Quiz not found.'}, 404
    current_question_id = get_current_question(quiz_id)
    current_question = get_question(current_question_id)
    answers = get_options_by_question(current_question_id)
    current_question['answers'] = answers
    if not current_question:
        return {'error': 'Current question not found.'}, 404
    return {'current_question': current_question}, 200
    

def get_top_participants(quiz_id, limit=10):
    """
    Retrieves the top participants for a given quiz based on their scores.

    :param quiz_id: מזהה החידון.
    :param limit: מספר המשתתפים המובילים להחזיר.
    :return: Tuple עם רשימת המשתתפים המובילים וקוד סטטוס HTTP.
    """
    try:
        participants = get_all_participants(quiz_id)
        if not participants:
            return {'error': 'אין משתתפים לחידון זה.'}, 404

        participant_scores = []
        for participant in participants:
            phone_number = participant['phone_number']
            answers = get_participant_answers(phone_number)
            score = calculate_score(answers)
            # אם יש לך דרך לקבל את שם המשתתף, שנה את השורה הבאה בהתאם
            participant_name = phone_number  # או get_user_name_by_phone(phone_number)
            participant_scores.append({'name': participant_name, 'points': score})

        # מיון המשתתפים לפי ניקוד יורד
        top_participants = sorted(participant_scores, key=lambda x: x['points'], reverse=True)[:limit]

        return {'top_participants': top_participants}, 200

    except Exception as e:
        print("Error in get_top_participants:", e)
        return {'error': 'שגיאה בשרת.'}, 500

