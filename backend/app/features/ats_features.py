from app.parsers.schemas import ParseResult
from app.parsers.resume_schema import ResumeData
from .schema import ATSFeatures

class ATSFeatureExtractor:
    @classmethod
    def extract(cls, parse_result: ParseResult, resume_data: ResumeData) -> ATSFeatures:
        # 1. CONTACT FEATURES
        ci = resume_data.contact_info
        email_val = 1.0 if ci.email else 0.0
        phone_val = 1.0 if ci.phone else 0.0
        linkedin_val = 0.8 if ci.linkedin_url else 0.0
        github_val = 0.6 if ci.github_url else 0.0
        portfolio_val = 0.3 if ci.website else 0.0
        
        raw_contact_score = email_val + phone_val + linkedin_val + github_val + portfolio_val
        contact_score = min(1.0, raw_contact_score / 3.7)  # max possible is 3.7

        # 2. SECTION PRESENCE
        has_summary = bool(resume_data.summary)
        has_education = bool(resume_data.education)
        has_experience = bool(resume_data.experience)
        has_skills = bool(resume_data.skills)
        has_projects = bool(resume_data.projects)
        has_certifications = bool(resume_data.certifications)
        has_achievements = bool(resume_data.achievements)

        sections_found = sum([has_summary, has_education, has_experience, has_skills, has_projects, has_certifications, has_achievements])
        section_completeness = sections_found / 7.0

        # 3. FORMAT PENALTY FEATURES
        flags = parse_result.ats_flags
        tables_penalty = -5.0 if flags.tables_detected else 0.0
        images_penalty = -8.0 if flags.images_detected else 0.0
        columns_penalty = -3.0 if flags.columns_detected else 0.0
        scanned_penalty = -15.0 if flags.is_scanned_pdf else 0.0
        total_format_penalty = tables_penalty + images_penalty + columns_penalty + scanned_penalty

        # 4. LENGTH FEATURES
        wc = parse_result.word_count
        if wc < 150:
            word_count_score = 0.0
        elif 150 <= wc < 300:
            word_count_score = (wc - 150) / 150.0
        elif 300 <= wc <= 800:
            word_count_score = 1.0
        else:
            word_count_score = max(0.0, 1.0 - (wc - 800) / 400.0)

        pc = parse_result.page_count
        if pc <= 2:
            page_score = 1.0
        elif pc == 3:
            page_score = 0.7
        else:
            page_score = 0.4

        # 5. DENSITY FEATURES
        exp_entries = resume_data.experience
        if exp_entries:
            total_bullets = sum(len(e.bullets) for e in exp_entries)
            bullets_per_job = total_bullets / len(exp_entries)
        else:
            bullets_per_job = 0.0
        bullets_score = min(1.0, bullets_per_job / 5.0)

        # 6. ATS SCORE FORMULA
        raw = (
            contact_score * 20.0 +
            section_completeness * 30.0 +
            word_count_score * 15.0 +
            page_score * 10.0 +
            bullets_score * 10.0 +
            25.0
        ) + total_format_penalty
        ats_score = max(0.0, min(100.0, raw))

        return ATSFeatures(
            has_email=bool(ci.email),
            has_phone=bool(ci.phone),
            has_linkedin=bool(ci.linkedin_url),
            has_github=bool(ci.github_url),
            has_summary=has_summary,
            has_education=has_education,
            has_experience=has_experience,
            has_skills=has_skills,
            has_projects=has_projects,
            contact_score=contact_score,
            section_completeness=section_completeness,
            tables_penalty=tables_penalty,
            images_penalty=images_penalty,
            columns_penalty=columns_penalty,
            scanned_penalty=scanned_penalty,
            total_format_penalty=total_format_penalty,
            word_count=wc,
            word_count_score=word_count_score,
            page_count=pc,
            page_score=page_score,
            bullets_per_job=bullets_per_job,
            bullets_score=bullets_score,
            ats_score=round(ats_score, 2)
        )
