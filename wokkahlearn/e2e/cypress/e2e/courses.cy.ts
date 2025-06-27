describe('Courses', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpassword123');
    cy.visit('/courses');
  });

  it('should display course list', () => {
    cy.contains('Browse Courses').should('be.visible');
    cy.get('[data-testid="course-card"]').should('have.length.at.least', 1);
  });

  it('should filter courses by difficulty', () => {
    cy.get('[data-testid="difficulty-filter"]').click();
    cy.get('[data-value="beginner"]').click();
    
    cy.get('[data-testid="course-card"]').each(($card) => {
      cy.wrap($card).should('contain', 'Beginner');
    });
  });

  it('should search for courses', () => {
    cy.get('[data-testid="search-input"]').type('Python');
    cy.get('[data-testid="search-button"]').click();
    
    cy.get('[data-testid="course-card"]').each(($card) => {
      cy.wrap($card).should('contain.text', 'Python');
    });
  });

  it('should enroll in a course', () => {
    cy.get('[data-testid="course-card"]').first().click();
    cy.get('[data-testid="enroll-button"]').click();
    
    cy.contains('Successfully enrolled').should('be.visible');
    cy.get('[data-testid="continue-button"]').should('be.visible');
  });

  it('should navigate through course content', () => {
    // Assuming user is enrolled in a course
    cy.get('[data-testid="enrolled-course"]').first().click();
    cy.get('[data-testid="lesson-item"]').first().click();
    
    cy.url().should('include', '/lessons/');
    cy.contains('Mark Complete').should('be.visible');
  });
});