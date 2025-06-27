describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should register a new user', () => {
    cy.get('[data-testid="register-button"]').click();
    
    cy.get('[name="username"]').type('testuser');
    cy.get('[name="email"]').type('test@example.com');
    cy.get('[name="firstName"]').type('Test');
    cy.get('[name="lastName"]').type('User');
    cy.get('[name="password"]').type('testpassword123');
    cy.get('[name="confirmPassword"]').type('testpassword123');
    
    cy.get('[type="submit"]').click();
    
    cy.url().should('include', '/login');
    cy.contains('Registration successful').should('be.visible');
  });

  it('should login with valid credentials', () => {
    cy.get('[data-testid="login-button"]').click();
    
    cy.get('[name="email"]').type('test@example.com');
    cy.get('[name="password"]').type('testpassword123');
    cy.get('[type="submit"]').click();
    
    cy.url().should('include', '/dashboard');
    cy.contains('Welcome back').should('be.visible');
  });

  it('should show error for invalid credentials', () => {
    cy.get('[data-testid="login-button"]').click();
    
    cy.get('[name="email"]').type('wrong@example.com');
    cy.get('[name="password"]').type('wrongpassword');
    cy.get('[type="submit"]').click();
    
    cy.contains('Invalid credentials').should('be.visible');
  });
});

