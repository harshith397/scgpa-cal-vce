import rawData from '../data/syllabus.json';

// Flatten the deep tree into an array of objects
export const getFlattenedData = () => {
    const flatSubjects = [];
    for (const [program, departments] of Object.entries(rawData)) {
        for (const [dept, semesters] of Object.entries(departments)) {
            for (const [sem, courses] of Object.entries(semesters)) {
                for (const [courseName, details] of Object.entries(courses)) {
                    flatSubjects.push({
                        program,
                        dept,
                        sem: parseInt(sem),
                        name: courseName,
                        code: details["COURSE CODE"],
                        credits: parseInt(details["CREDITS"])
                    });
                }
            }
        }
    }
    return flatSubjects;
};

// Helper functions for dropdown population
export const getPrograms = () => Object.keys(rawData);
export const getDepartments = (program) => program ? Object.keys(rawData[program]) : [];
export const getSemesters = (program, dept) => (program && dept) ? Object.keys(rawData[program][dept]) : [];