from .models import db, Competency, Module

def load_competencies_and_modules():
    # If already populated, skip
    if Competency.query.first():
        return

    # Competencies and modules as per your initial mapping/specs
    competencies = [
        {
            "key": "A",
            "name": "High Performance Computing",
            "description": "Master the fundamentals and advanced concepts of high-performance computing systems and applications.",
            "modules": [
                {"key": "A1", "name": "Estimate benefit of HPC on specific use case", "description": ""},
                {"key": "A2", "name": "Running specific software/tool/workflow on HPC environments", "description": ""},
                {"key": "A3", "name": "Performance optimization on HPC", "description": ""},
                {"key": "A4", "name": "Debugging software/workflow on HPC", "description": ""},
                {"key": "A5", "name": "Operating HPC system", "description": ""},
            ]
        },
        {
            "key": "B",
            "name": "Computing",
            "description": "Build expertise in computational tools, environments, and resource management.",
            "modules": [
                {"key": "B1", "name": "Working remotely in Linux environment via command line interface", "description": ""},
                {"key": "B2", "name": "Managing programming languages and their packages via package manager", "description": ""},
                {"key": "B3", "name": "Installing and managing scientific software and preparing a related environment", "description": ""},
                {"key": "B4", "name": "Using specific tools, software, or IDEs as each individual or together", "description": ""},
                {"key": "B5", "name": "Estimating computing resource requirement", "description": ""},
                {"key": "B6", "name": "Distribute software, data, or trained model", "description": ""},
            ]
        },
        {
            "key": "C",
            "name": "Law and Compliance",
            "description": "Compliance with license, policy, and ethics.",
            "modules": [
                {"key": "C1", "name": "Compliance with license, policy, and ethics", "description": ""},
            ]
        },
        {
            "key": "D",
            "name": "Research",
            "description": "Scientific background knowledge, Methodology, process, and tools.",
            "modules": [
                {"key": "D1", "name": "Scientific background knowledge, Methodology, process, and tools", "description": ""},
                {"key": "D2", "name": "Literature Review", "description": ""},
                {"key": "D3", "name": "Scientific Data management and analysis", "description": ""},
            ]
        },
        {
            "key": "E",
            "name": "Soft skills",
            "description": "Teamwork, Communication, and Human-driven service provision and support.",
            "modules": [
                {"key": "E1", "name": "Teamwork", "description": ""},
                {"key": "E2", "name": "Communication", "description": ""},
                {"key": "E3", "name": "Human-driven service provision and support", "description": ""},
            ]
        }
    ]

    for comp in competencies:
        c = Competency(key=comp["key"], name=comp["name"], description=comp["description"])
        db.session.add(c)
        db.session.commit()
        for idx, m in enumerate(comp["modules"]):
            module = Module(
                key=m["key"], name=m["name"], description=m["description"],
                competency_id=c.id, order=idx
            )
            db.session.add(module)
        db.session.commit()
from .models import db, Competency, Module

def load_competencies_and_modules():
    # If already populated, skip
    if Competency.query.first():
        return

    # Competencies and modules as per your initial mapping/specs
    competencies = [
        {
            "key": "A",
            "name": "High Performance Computing",
            "description": "Master the fundamentals and advanced concepts of high-performance computing systems and applications.",
            "modules": [
                {"key": "A1", "name": "Estimate benefit of HPC on specific use case", "description": ""},
                {"key": "A2", "name": "Running specific software/tool/workflow on HPC environments", "description": ""},
                {"key": "A3", "name": "Performance optimization on HPC", "description": ""},
                {"key": "A4", "name": "Debugging software/workflow on HPC", "description": ""},
                {"key": "A5", "name": "Operating HPC system", "description": ""},
            ]
        },
        {
            "key": "B",
            "name": "Computing",
            "description": "Build expertise in computational tools, environments, and resource management.",
            "modules": [
                {"key": "B1", "name": "Working remotely in Linux environment via command line interface", "description": ""},
                {"key": "B2", "name": "Managing programming languages and their packages via package manager", "description": ""},
                {"key": "B3", "name": "Installing and managing scientific software and preparing a related environment", "description": ""},
                {"key": "B4", "name": "Using specific tools, software, or IDEs as each individual or together", "description": ""},
                {"key": "B5", "name": "Estimating computing resource requirement", "description": ""},
                {"key": "B6", "name": "Distribute software, data, or trained model", "description": ""},
            ]
        },
        {
            "key": "C",
            "name": "Law and Compliance",
            "description": "Compliance with license, policy, and ethics.",
            "modules": [
                {"key": "C1", "name": "Compliance with license, policy, and ethics", "description": ""},
            ]
        },
        {
            "key": "D",
            "name": "Research",
            "description": "Scientific background knowledge, Methodology, process, and tools.",
            "modules": [
                {"key": "D1", "name": "Scientific background knowledge, Methodology, process, and tools", "description": ""},
                {"key": "D2", "name": "Literature Review", "description": ""},
                {"key": "D3", "name": "Scientific Data management and analysis", "description": ""},
            ]
        },
        {
            "key": "E",
            "name": "Soft skills",
            "description": "Teamwork, Communication, and Human-driven service provision and support.",
            "modules": [
                {"key": "E1", "name": "Teamwork", "description": ""},
                {"key": "E2", "name": "Communication", "description": ""},
                {"key": "E3", "name": "Human-driven service provision and support", "description": ""},
            ]
        }
    ]

    for comp in competencies:
        c = Competency(key=comp["key"], name=comp["name"], description=comp["description"])
        db.session.add(c)
        db.session.commit()
        for idx, m in enumerate(comp["modules"]):
            module = Module(
                key=m["key"], name=m["name"], description=m["description"],
                competency_id=c.id, order=idx
            )
            db.session.add(module)
        db.session.commit()

def get_learning_objective(role, module_key, current_level):
    objectives = {
        "ai_specialist": {
            "A1": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "A2": {"Apprentice": "remember", "Practitioner": "apply", "Competent": "analyze"},
            "A3": {"Practitioner": "understand", "Competent": "apply"},
            "A4": {},
            "A5": {},
            "B1": {"Apprentice": "apply", "Practitioner": "apply", "Competent": "evaluate"},
            "B2": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "analyze"},
            "B3": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "understand"},
            "B4": {"Apprentice": "Apply", "Practitioner": "Apply", "Competent": "Analyze"},
            "B5": {"Apprentice": "remember", "Practitioner": "Apply", "Competent": "Analyze"},
            "B6": {},
            "C1": {"Apprentice": "understand", "Practitioner": "understand", "Competent": "apply"},
            "D1": {"Apprentice": "understand", "Practitioner": "understand", "Competent": "apply"},
            "D2": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "D3": {"Apprentice": "apply", "Practitioner": "apply", "Competent": "apply"},
            "E1": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "evaluate"},
            "E2": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "create"},
            "E3": {}
        },
        "comp_chem_specialist": {
            "A1": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "A2": {"Apprentice": "remember", "Practitioner": "apply", "Competent": "analyze"},
            "A3": {"Practitioner": "understand", "Competent": "apply"},
            "A4": {},
            "A5": {},
            "B1": {"Apprentice": "apply", "Practitioner": "apply", "Competent": "evaluate"},
            "B2": {"Competent": "apply"},
            "B3": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "B4": {},
            "B5": {},
            "B6": {},
            "C1": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "D1": {"Apprentice": "understand", "Practitioner": "understand", "Competent": "apply"},
            "D2": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "D3": {"Apprentice": "apply", "Practitioner": "apply", "Competent": "apply"},
            "E1": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "evaluate"},
            "E2": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "create"},
            "E3": {}
        }
    }
    return objectives.get(role, {}).get(module_key, {}).get(current_level, "N/A")

