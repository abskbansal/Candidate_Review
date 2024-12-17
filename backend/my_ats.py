import re

def evaluate_resume_content(file_content):
    """
    Evaluate the general quality of a resume for ATS by checking skills, experience, 
    education, sections, and overall textual quality.

    :param file_content: Resume content as a byte string (text format).
    :return: A dictionary with detailed scoring breakdown and total score.
    """
    try:
        # Decode the resume content
        resume_text = file_content.decode('utf-8', errors='ignore').lower()

        # Initialize score components
        skills_score = 0
        experience_score = 0
        education_score = 0
        certification_score = 0
        section_score = 0
        quality_score = 0

        # ---- Skills Matching (Generic Skills) ----
        generic_skills = ['python', 'java', 'sql', 'html', 'css', 'javascript', 'aws', 'cloud', 'leadership', 'project management']
        
        for skill in generic_skills:
            if skill in resume_text:
                skills_score += 5  # Each matched skill adds 5 points

        # ---- Experience Matching ----
        experience_score = 0
        experience_keywords = ['managed', 'led', 'developed', 'designed', 'implemented', 'created', 'coordinated']
        
        # Count how many experience-related action verbs are used
        experience_score = sum(resume_text.count(word) for word in experience_keywords)

        # ---- Education Matching ----
        education_score = 0
        education_levels = ['bachelor', 'master', 'phd', 'degree', 'diploma']
        
        for level in education_levels:
            if level in resume_text:
                education_score += 10  # Education match adds 10 points

        # ---- Certification Matching ----
        certification_score = 0
        certifications = ['aws', 'certified', 'pmp', 'scrum master', 'google cloud']
        
        for cert in certifications:
            if cert in resume_text:
                certification_score += 10  # Certification match adds 10 points

        # ---- Section Detection ----
        sections = ['experience', 'education', 'skills', 'certifications']
        section_matches = sum(1 for section in sections if section in resume_text)
        section_score = section_matches * 10  # 10 points for each section found

        # ---- Quality of Resume ----
        # Check if the resume is sufficiently long (generally at least 300 words)
        word_count = len(resume_text.split())
        quality_score = 0
        if word_count > 300:
            quality_score = 10  # Bonus for longer resumes (usually more detailed)

        # ---- Total Score Calculation ----
        total_score = skills_score + experience_score + education_score + certification_score + section_score + quality_score

        # Cap the total score at 100
        total_score = min(100, total_score)

        # Detailed score breakdown
        score_breakdown = {
            "skills_score": skills_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "certification_score": certification_score,
            "section_score": section_score,
            "quality_score": quality_score
        }

        return {"total_score": total_score, "score_breakdown": score_breakdown}

    except Exception as e:
        print(f"Error processing resume content: {e}")
        return {"total_score": 0, "score_breakdown": {}}
