rem ### CODE OWNERS: Shea Parkes, Steve Gredell
rem
rem ### OBJECTIVE:
rem   Do minimal environment setup
rem
rem ### DEVELOPER NOTES:
rem   Desired to be as lean as possible since this should be solution agnostic

echo %~nx0 %DATE:~-4%-%DATE:~4,2%-%DATE:~7,2% %TIME%: Setting up environment for usage/testing
echo %~nx0 %DATE:~-4%-%DATE:~4,2%-%DATE:~7,2% %TIME%: Running from %~f0

rem ### LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE


echo %~nx0 %DATE:~-4%-%DATE:~4,2%-%DATE:~7,2% %TIME%: Calling current Pipeline_Components_Env
call S:\PRM\Pipeline_Components_Env\pipeline_components_env.bat

echo %~nx0 %DATE:~-4%-%DATE:~4,2%-%DATE:~7,2% %TIME%: Finished setting up environment for usage/testing
