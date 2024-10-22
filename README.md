konquista.com.br
Konquista: Lead Relationship Management System

Overview

Full-featured CRM (Customer Relationship Management) project designed to streamline lead management and communication via WhatsApp. 

The system focuses on automating personalized message delivery, managing leads, and integrating advanced APIs to ensure efficient lead nurturing and engagement. It provides a complete suite of tools, including CSV upload, real-time analytics, and an intuitive user interface for administrators.

Built using advanced fullstack technologies, WhatsLab showcases complex systems integration, custom API development, and seamless front-end and back-end synchronization.

Features

1. Personalized Message Management

	•	Full CRUD: Create, edit, view, and delete personalized messages to be sent to leads through WhatsApp.
	•	API Integration (APISocialHub): Messages are integrated with the WhatsApp API through the APISocialHub component, allowing for direct message sending with real-time validation and preview.
	•	Dynamic Forms: WTForms manages form validation and handles front-end data to ensure smooth interaction.

2. Phone Number Management

	•	CRUD for User Phones: Users can register phone numbers and tokens, facilitating secure message sending.
	•	API Integration: Each phone is securely registered with a token, managed through the APICrmGraphQL component, allowing personalized message flow per user phone.

3. Lead Management via CSV and Dynamic Landing Pages

	•	CSV Upload: Mass lead import through CSV files, streamlining data ingestion.
	•	Dynamic Landing Pages: The LeadGen component dynamically generates landing pages to capture leads. The captured leads automatically flow into the message dispatch pipeline, enhancing lead conversion.
	•	Real-Time Lead Flow: As leads are generated, they are automatically placed into the message workflow, powered by GraphQL mutations for immediate integration.

4. Custom GraphQL API

	•	CRUD Operations on Leads: Using Graphene, a custom GraphQL API has been developed to handle lead creation, updates, and deletions via mutations, providing flexibility for third-party integrations.
	•	Query Leads and Messages: APICrmGraphQL handles querying leads, messages, and phone data, enabling custom dashboards and analytics views in real-time.

5. DataWrestler Component

	•	Data Processing: The DataWrestler component processes and merges lead data from various sources (e.g., WhatsApp, landing pages) with appointment and messaging history to ensure data consistency and accurate message targeting.
	•	Analytics and Metrics: Custom-built logic aggregates lead data, tracks message success, and dynamically analyzes lead engagement, making WhatsLab an intelligent lead management platform.

6. User-Friendly Interface

	•	Bootstrap-Driven UI: A responsive and clean user interface ensures a seamless experience across devices.
	•	Navigation and Control: The admin interface is equipped with intuitive buttons for managing messages, leads, and phone numbers, making complex actions simple and efficient for the user.

Key Components

1. APISocialHub (WhatsApp API Integration)

Handles WhatsApp message dispatch with validations for preview, error handling, and success logging. It integrates seamlessly with the backend to automate message workflows for the registered leads and phone numbers.

2. APICrmGraphQL

Developed using Graphene, this custom GraphQL API allows for flexible CRUD operations on leads and messages. It serves as the primary interface for data retrieval and modification within the WhatsLab system, making it highly scalable and open for integration with external systems.

3. DataWrestler

A powerful internal data processing component that merges and processes data from multiple sources (leads, appointments, message logs) to produce a unified, actionable dataset. DataWrestler is responsible for optimizing lead engagement strategies by ensuring the data is complete and accurate.

4. LeadGen

A dynamic landing page generator that captures leads from multiple sources and injects them directly into the CRM’s workflow. It allows for customizable landing pages based on different lead sources and marketing campaigns, automatically integrating with APISocialHub for message dispatch.

Technologies Used

Back-End

	•	Flask (Python): Handles routing, business logic, and API interactions.
	•	SQLAlchemy: ORM for interacting with the PostgreSQL database.
	•	Graphene (GraphQL): Provides a flexible and efficient GraphQL API to manage leads and messages.
	•	Flask-Migrate: Manages database schema changes with automated migrations.
	•	Flask-WTForms: Used for form handling and validation across the entire user interface.

Front-End

	•	Bootstrap 4: Responsive front-end framework.
	•	Jinja2: Templating engine for rendering dynamic content in HTML.
	•	Font Awesome: Icons to enhance user experience.

Database

	•	PostgreSQL: Relational database to store leads, messages, and user phones.
	•	Supabase: Remote database storage for secure and scalable data management.

Integrations

	•	WhatsApp API (APISocialHub): Allows sending personalized WhatsApp messages to leads, managed by the APISocialHub component.
	•	GraphQL API (APICrmGraphQL): Custom GraphQL API for advanced querying and mutation of leads and messages.
	•	CSV Upload: Bulk lead import via CSV to facilitate large-scale lead management.

Deployment

	•	Vercel: Continuous integration and deployment using GitHub, ensuring fast and smooth production deployment.
	•	Git and GitHub: Version control for efficient development and collaboration.

How It Works

	1.	Message Management: Admins can create, edit, and delete personalized messages that will be sent to leads via the WhatsApp API.
	2.	Phone Number Registration: Users can register their phone numbers and tokens, which are securely stored and used for message dispatch.
	3.	Lead Management: Admins can upload leads via CSV files or dynamically capture them via landing pages. These leads are automatically integrated into message workflows.
	4.	Automated Message Sending: Once a lead is in the system, APISocialHub takes over and ensures that messages are delivered based on the preset campaign rules.
	5.	Data Processing: DataWrestler processes and merges lead data from various sources, allowing for real-time analysis and optimized message dispatch.