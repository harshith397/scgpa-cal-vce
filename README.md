# VCE SGPA Calculator

A static site SGPA calculator designed for the students of Vasavi College of Engineering.

## Live Demo
*[link]*

## Key Features

* **Algorithmic Efficiency:** Utilizes a one-time $O(N)$ JSON flattening parser on load, and an $O(1)$ Hash Map to track grade slider updates, ensuring zero UI thread blocking.
* **Native iOS Aesthetic:** Custom-built CSS adhering to Apple's Human Interface Guidelines.
* **Opt-Out Selection UX:** Automatically populates the core subjects for a selected semester, allowing students to remove unused electives/subjects rather than manually adding every course.
* **Zero Backend:** 100% static architecture.

## Tech Stack

* **Core:** React 18
* **Build Tool:** Vite (Native ES Modules for instantaneous HMR)
* **Styling:** Vanilla CSS (CSS Variables, Flexbox, Media Queries)
* **Data:** Local JSON payload (Normalized at runtime)

## Architecture & State Management

Instead of traversing a deeply nested JSON tree (`Program -> Dept -> Sem -> Subject`) on every user interaction, the app employs a **Normalization Strategy**. 

1. **The Parser:** Flattens the hierarchical syllabus data into a single 1D array of subject objects.
2. **Cascading State:** Upstream dropdowns (Program) explicitly invalidate and wipe downstream states (Semester, Grades) to prevent data collisions and mathematically impossible SGPA outputs.
3. **Identifier Safety:** Uses a two-pass Regex Title Case formatter and relies on `subject.name` as the primary key to prevent identifier collisions among open electives that share placeholder course codes.

## Local Development Setup

To run this project locally:

1. **Clone the repository:**
   ```bash
   git clone 
   https://github.com/harshith397/scgpa-cal-vce.git
   cd vce-sgpa-calc
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the Vite development server:**
   ```bash
   npm run dev
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

## Author
**Medichelme Harshith** Computer Science Engineering Undergraduate - Vasavi College of Engineering