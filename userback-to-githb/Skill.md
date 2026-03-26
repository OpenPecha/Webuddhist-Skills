# **Skill Name: Userback-to-GitHub Requirements Engineer**

## **Objective**

Automatically synchronize "Open" feedback from a Userback Public Roadmap to a GitHub Repository, transforming raw user feedback into structured Developer Tickets (User Stories).

## **Logic Flow**

1. **Extraction**: Access the provided Userback Roadmap URL.  
2. **Filtering**: Identify all entries currently in the "Open" status.  
3. **Analysis**: For each item, analyze the title, description, and any attached media (images/videos).  
4. **Transformation**: Use the LLM to convert the raw input into the defined ticket template.  
5. **Execution**:  
   * Create a new Issue in the target GitHub Repository.  
   * Attach the GitHub Issue to the specified Project Board.  
   * Move the project item to the "To Do" column.

## **Ticket Template (Markdown)**

The bot must generate the ticket body using this exact structure:

### **Title**

\[Concise, technical title\]

**As** \[User Type/Role\]

**I want** \[Action/Requirement\]

**So that** \[Value/Benefit\]

### **Description**

\[A summary of the user feedback and context provided in the Userback item.\]

### **Scope of Work**

* \[Technical task 1\]  
* \[Technical task 2\]  
* \[Technical task 3\]

### **Acceptance Criteria**

* \[ \] \[Metric or condition for success 1\]  
* \[ \] \[Metric or condition for success 2\]  
* \[ \] \[Metric or condition for success 3\]

### **Definition of Done**

* \[Code reviewed\]  
* \[Tests passed\]  
* \[Documentation updated\]

## **Tool Requirements**

* **GitHub PAT (Personal Access Token)**: With repo and project scopes.  
* **Userback Roadmap Access**: Ability to parse the public roadmap JSON or HTML.  
* **Project ID & Column Name**: To ensure the issue lands in the correct workflow stage.