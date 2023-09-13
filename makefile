run:
	python	./simulator.py inst.txt data.txt config.txt result.txt

clean:
	rm -f ./*.pyc
	rm -f ./modules/*.pyc
	rm -rf ./modules/__pycache__
	rm -f result.txt
	rm -f ./__pycache__/*
