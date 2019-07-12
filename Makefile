SET_USER?=		${USER}
JMANAGER_COMMAND=	python3.6 -m jmanager
JMANAGER_OPTIONS=	--jmanager-config src/test/resources/jmanager.conf

LIST_TYPE=jail

pre-test:
	scripts/zfs_init.sh ${SET_USER}
test: pre-test
	pipenv run pytest --cov-report html --cov=src --cov=models

test_commands: test_help test_create test_destroy

check_test_commands:
	if [ "$$(uname -o)" != "FreeBSD" ] ; then \
		echo "FreeBSD only!" >&2; \
		exit 1 ; \
	fi
	if [ "$$(id -u)" -ne 0 ] ; then \
		echo "Must be run as root!" >&2 ;\
		exit 1 ; \
	fi

test_help:
	python3.6 -m jmanager --help >> /dev/null
	python3.6 -m jmanager create --help >> /dev/null
	python3.6 -m jmanager destroy --help >> /dev/null
	python3.6 -m jmanager list --help >> /dev/null

test_create: check_test_commands
	${JMANAGER_COMMAND} ${JMANAGER_OPTIONS} \
		create examples/JManagerFile

test_destroy: check_test_commands test_create
	${JMANAGER_COMMAND} ${JMANAGER_OPTIONS} \
		destroy example

test_list:
	${JMANAGER_COMMAND} ${JMANAGER_OPTIONS} \
		list --type ${LIST_TYPE}
