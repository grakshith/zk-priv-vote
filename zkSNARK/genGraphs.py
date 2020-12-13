import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
# sns.set_theme(style="whitegrid")
sns.set(font_scale = 2)
# plt.rcParams["axes.labelsize"] = 15

fig = plt.figure(figsize=(16,16))
ax = fig.add_subplot(111)
# Total time
x = ['a_2_c', 'a_2_v', 'a_1_c', 'a_1_v', 'na_2_c', 'na_2_v', 'na_1_c', 'na_1_v']
y = [246.063, 250.069, 150.984, 146.275, 132.25, 131.882, 130.84, 131.492]
times = pd.DataFrame()
times['scenario'] = x
times['total_process_time'] = y
ax = sns.barplot(x="scenario", y="total_process_time", data=times, palette="Blues_d")
ax.set_title('Total Time vs. Scenario')
ax.set_xlabel('scenario')
ax.set_ylabel('total process time (s)')
plt.savefig('totaltime.png')
plt.show()

fig = plt.figure(figsize=(16,16))
ax0 = fig.add_subplot(121)
#Proving time
y = [0.042, 0.023]
x = ['a_2_c', 'a_2_v']
times = pd.DataFrame()
times['scenario'] = x
times['proving_time'] = y
ax0 = sns.barplot(x="scenario", y="proving_time", data=times, palette="Blues_d", ax = ax0)
ax0.set_title('Proving Time vs. Scenario')
ax0.set_xlabel('scenario')
ax0.set_ylabel('proving time (s)')
plt.savefig('provingtime.png')
plt.show()

fig = plt.figure(figsize=(16,16))
ax1 = fig.add_subplot(121)
#Verifying time
x = ['a_2_v', 'a_1_v']
y = [0.041, 0.026]
times = pd.DataFrame()
times['scenario'] = x
times['verification_time'] = y
ax1 = sns.barplot(x="scenario", y="verification_time", data=times, palette="Blues_d", ax = ax1)
ax1.set_title('Verification Time vs. Scenario')
ax1.set_xlabel('scenario')
ax1.set_ylabel('verification time (s)')
plt.savefig('verifyingtime.png')
plt.show()