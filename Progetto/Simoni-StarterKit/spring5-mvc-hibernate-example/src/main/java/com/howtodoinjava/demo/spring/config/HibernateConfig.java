package com.howtodoinjava.demo.spring.config;

import com.howtodoinjava.demo.spring.model.Component;
import org.apache.commons.dbcp.BasicDataSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.core.env.Environment;
import org.springframework.orm.hibernate5.HibernateTransactionManager;
import org.springframework.orm.hibernate5.LocalSessionFactoryBean;
import org.springframework.transaction.annotation.EnableTransactionManagement;


import javax.sql.DataSource;
import java.util.Properties;


@Configuration
@EnableTransactionManagement
@PropertySource({ "classpath:persistence-mysql.properties" })
@ComponentScan({ "com.howtodoinjava.demo.spring" })
public class HibernateConfig {

//	@Autowired
//	private ApplicationContext context;
//
//	@Bean
//	public LocalSessionFactoryBean getSessionFactory() {
//		LocalSessionFactoryBean factoryBean = new LocalSessionFactoryBean();
//		factoryBean.setConfigLocation(context.getResource("classpath:hibernate.cfg.xml"));
//		factoryBean.setAnnotatedClasses(User.class);
//		return factoryBean;
//	}
//
//	@Bean
//	public HibernateTransactionManager getTransactionManager() {
//		HibernateTransactionManager transactionManager = new HibernateTransactionManager();
//		transactionManager.setSessionFactory(getSessionFactory().getObject());
//		return transactionManager;
//	}

	/**===========================================================================================*/

//	@Autowired
//	private Environment environment;
//
//	/************* Start Spring JPA config details **************/
//	@Bean(name = "entityManagerFactory")
//	public LocalContainerEntityManagerFactoryBean getEntityManagerFactoryBean() {
//		LocalContainerEntityManagerFactoryBean lcemfb = new LocalContainerEntityManagerFactoryBean();
//		lcemfb.setJpaVendorAdapter(getJpaVendorAdapter());
//		lcemfb.setDataSource(dataSource());
//		lcemfb.setPersistenceUnitName("myJpaPersistenceUnit");
//		lcemfb.setPackagesToScan("com.javaspringclub");
//		lcemfb.setJpaProperties(hibernateProperties());
//		return lcemfb;
//	}
//
//	@Bean
//	public JpaVendorAdapter getJpaVendorAdapter() {
//		JpaVendorAdapter adapter = new HibernateJpaVendorAdapter();
//		return adapter;
//	}

//	@Bean(name = "transactionManager")
//	public PlatformTransactionManager txManager() {
//		JpaTransactionManager jpaTransactionManager = new JpaTransactionManager(
//				getEntityManagerFactoryBean().getObject());
//		return jpaTransactionManager;
//	}

	/************* End Spring JPA config details **************/

//	@Bean(name = "dataSource")
//	public DataSource dataSource() {
//		DriverManagerDataSource dataSource = new DriverManagerDataSource();
//		dataSource.setDriverClassName(environment.getRequiredProperty("jdbc.driver"));
//		dataSource.setUrl(environment.getRequiredProperty("jdbc.url"));
//		dataSource.setUsername(environment.getRequiredProperty("jdbc.username"));
//		dataSource.setPassword(environment.getRequiredProperty("jdbc.password"));
//		return dataSource;
//	}
//
//	private Properties hibernateProperties() {
//		Properties properties = new Properties();
//		properties.put("hibernate.dialect", environment.getRequiredProperty("hibernate.dialect"));
//		properties.put("hibernate.show_sql", environment.getRequiredProperty("hibernate.show_sql"));
//		properties.put("hibernate.format_sql", environment.getRequiredProperty("hibernate.format_sql"));
//		properties.put("hibernate.hbm2ddl.auto", environment.getRequiredProperty("hibernate.hbm2ddl.auto"));
//		return properties;
//	}

	/**========================================================================================*/




//		@Autowired
//		private Environment env;
//
//		@Bean
//		public LocalSessionFactoryBean sessionFactory() {
//			LocalSessionFactoryBean sessionFactory = new LocalSessionFactoryBean();
//			sessionFactory.setDataSource(restDataSource());
//			sessionFactory.setPackagesToScan(
//					new String[] { "com.howtodoinjava.demo.spring.model" });
//			sessionFactory.setHibernateProperties(hibernateProperties());
//
//			return sessionFactory;
//		}
//
//		@Bean
//		public DataSource restDataSource() {
//			BasicDataSource dataSource = new BasicDataSource();
//			dataSource.setDriverClassName(env.getProperty("jdbc.driverClassName"));
//			dataSource.setUrl(env.getProperty("jdbc.url"));
//			dataSource.setUsername(env.getProperty("jdbc.user"));
//			dataSource.setPassword(env.getProperty("jdbc.pass"));
//
//			return dataSource;
//		}
//
//		@Bean
//		@Autowired
//		public HibernateTransactionManager transactionManager(
//				SessionFactory sessionFactory) {
//
//			HibernateTransactionManager txManager
//					= new HibernateTransactionManager();
//			txManager.setSessionFactory(sessionFactory);
//
//			return txManager;
//		}
//
//		@Bean
//		public PersistenceExceptionTranslationPostProcessor exceptionTranslation() {
//			return new PersistenceExceptionTranslationPostProcessor();
//		}
//
//		Properties hibernateProperties() {
//			return new Properties() {
//				{
//					setProperty("hibernate.hbm2ddl.auto", env.getProperty("hibernate.hbm2ddl.auto"));
//					setProperty("hibernate.dialect", env.getProperty("hibernate.dialect"));
//					setProperty("hibernate.globally_quoted_identifiers", "true");
//				}
//			};
//		}

	@Autowired
	private Environment env;

	@Bean
	public DataSource getDataSource() {
		BasicDataSource dataSource = new BasicDataSource();
		dataSource.setDriverClassName(env.getProperty("db.driver"));
		dataSource.setUrl(env.getProperty("db.url"));
		dataSource.setUsername(env.getProperty("db.username"));
		dataSource.setPassword(env.getProperty("db.password"));

		return dataSource;
	}

	@Bean
	public LocalSessionFactoryBean getSessionFactory() {
		LocalSessionFactoryBean factoryBean = new LocalSessionFactoryBean();
		factoryBean.setDataSource(getDataSource());

		Properties props=new Properties();
		props.put("hibernate.show_sql", env.getProperty("hibernate.show_sql"));
		props.put("hibernate.hbm2ddl.auto", env.getProperty("hibernate.hbm2ddl.auto"));
		props.put("hibernate.dialect", env.getProperty("hibernate.dialect"));
		props.put("hibernate.format_sql", env.getProperty("hibernate.format_sql"));

		factoryBean.setHibernateProperties(props);
		factoryBean.setAnnotatedClasses(Component.class);
		//factoryBean.setAnnotatedClasses(Computation.class);
		return factoryBean;
	}

	@Bean
	public HibernateTransactionManager getTransactionManager() {
		HibernateTransactionManager transactionManager = new HibernateTransactionManager();
		transactionManager.setSessionFactory(getSessionFactory().getObject());
		return transactionManager;
	}
	}

