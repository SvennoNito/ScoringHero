fid = fopen('C:\PhDScripts\Sides\ScoringHero\example_data\example_data.json', 'rt');
rawData = fread(fid, inf, '*char');
fclose(fid);
strData = string(rawData');
scoring = jsondecode(strData);