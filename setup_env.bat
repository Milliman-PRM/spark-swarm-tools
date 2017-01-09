@echo off
rem ### CODE OWNERS: Shea Parkes, Steve Gredell
rem
rem ### OBJECTIVE:
rem   Do minimal environment setup
rem
rem ### DEVELOPER NOTES:
rem   Desired to be as lean as possible since this should be solution agnostic
rem   Also runs with very limited network access in production

echo %~nx0 %DATE:~-4%-%DATE:~4,2%-%DATE:~7,2% %TIME%: Setting up environment for usage/testing
echo %~nx0 %DATE:~-4%-%DATE:~4,2%-%DATE:~7,2% %TIME%: Running from %~f0

rem ### LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE


set CONDA_ENVIRONMENT=prod2016_11
echo %~nx0 %DATE:~-4%-%DATE:~4,2%-%DATE:~7,2% %TIME%: Activating %CONDA_ENVIRONMENT% conda environment
call activate prod2016_11

echo %~nx0 %DATE:~-4%-%DATE:~4,2%-%DATE:~7,2% %TIME%: Finished setting up environment for usage/testing
