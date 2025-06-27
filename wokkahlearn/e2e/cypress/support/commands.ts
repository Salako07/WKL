declare namespace Cypress {
  interface Chainable {
    login(email: string, password: string): Chainable<void>;
    createCourse(courseData: any): Chainable<void>;
    enrollInCourse(courseId: string): Chainable<void>;
  }
}

Cypress.Commands.add('login', (email: string, password: string) => {
  cy.session([email, password], () => {
    cy.visit('/login');
    cy.get('[name="email"]').type(email);
    cy.get('[name="password"]').type(password);
    cy.get('[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });
});

Cypress.Commands.add('createCourse', (courseData) => {
  cy.request({
    method: 'POST',
    url: '/api/courses/',
    body: courseData,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('accessToken')}`,
    },
  });
});

Cypress.Commands.add('enrollInCourse', (courseId: string) => {
  cy.request({
    method: 'POST',
    url: `/api/courses/${courseId}/enroll/`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('accessToken')}`,
    },
  });
});
